#include <array>
#include <cerrno>
#include <filesystem>
#include <iostream>
#include <iterator>
#include <optional>
#include <string>
#include <unordered_set>

#include <grp.h>
#include <pwd.h>
#include <unistd.h>

namespace fs = std::filesystem;
using std::cerr;
using namespace std::string_literals;

static std::optional<std::string> prog;
static constexpr std::array pos_args = {"MOUNT", "GROUP"};
static const fs::path mount{"/mnt"};

static void prog_error() { cerr << *prog << ": error: "; }

static void prog_usage() {
  cerr << "usage: " << *prog << " [-h|--help]";
  for (const auto &arg : pos_args) {
    cerr << " " << arg;
  }
  cerr << "\n";
}

static bool recursive(fs::path p) {
  std::unordered_set<fs::path> visited;
  while (is_symlink(p) && visited.find(p) == visited.end()) {
    visited.insert(p);
    p = fs::read_symlink(p);
  }
  return is_symlink(p);
}

static bool apply(fs::directory_entry const &entry,
                  std::unordered_set<fs::path> &visited, unsigned depth,
                  fs::path const &starting_dir, uid_t const &uid,
                  gid_t const &gid) {

  fs::path const &path = entry.path();
  if (recursive(path))
    return true;

  bool is_regular_file = false, is_directory = false;
  fs::file_status const status = entry.status();
  switch (status.type()) {
    case fs::file_type::regular:
      is_regular_file = true;
      break;
    case fs::file_type::directory:
      is_directory = true;
      break;
    default:
      return true;
  }

  fs::path const canonical_path = fs::canonical(path);
  if (visited.find(canonical_path) != visited.end())
    return true;

  bool result;
  {
    auto a = canonical_path.begin(), b = starting_dir.begin();
    while (a != canonical_path.end() && b != starting_dir.end() && *a == *b) {
      ++a;
      ++b;
    }
    if (b != starting_dir.end()) {
      result = false;
      goto cache_end;
    }
  }

  if (chown(canonical_path.c_str(), uid, gid))
    throw fs::filesystem_error("cannot set ownership", path,
                               {errno, std::system_category()});

  if (is_directory && path.filename() == ".git") {
    result = true;
    goto cache_end;
  }

  {
    fs::perms const original_perms = status.permissions();
    fs::perms perms = original_perms & fs::perms::owner_all;

    if (is_regular_file &&
        canonical_path.filename().extension() == ".sh")
      perms |= fs::perms::owner_exec;

    if (static_cast<bool>(perms & fs::perms::owner_read)) {
      perms |= fs::perms::group_read;
      if (is_regular_file) {
        fs::path const relative_path =
            canonical_path.lexically_relative(starting_dir);
        if (depth)
          perms |= fs::perms::others_read;
      }
    }
    if (static_cast<bool>(perms & fs::perms::owner_exec)) {
      perms |= fs::perms::group_exec;
      if (is_directory || depth)
        perms |= fs::perms::others_exec;
    }

    if (perms != original_perms)
      fs::permissions(path, perms);
  }
  result = false;

cache_end:
  visited.insert(canonical_path);

  return result;
}

int main(int argc, char *argv[]) {

  prog = fs::path(argv[0]).filename();

  for (unsigned i = 1; i < (unsigned)argc; ++i) {
    if (argv[i] == "-h"s || argv[i] == "--help"s) {
      prog_usage();
      cerr << "\n"
           << "positional arguments:\n"
           << "  MOUNT        mount directory\n"
           << "  GROUP        group name to set files to\n"
           << "\n"
           << "options:\n"
           << "  -h, --help   show this help message and exit\n";
      return 0;
    }
  }

  if ((unsigned)argc < 1 + pos_args.size()) {
    prog_usage();
    prog_error();
    cerr << "the following arguments are required:";
    for (unsigned i = argc - 1; i < pos_args.size(); ++i)
      cerr << " " << pos_args[i];
    cerr << "\n";
    return 2;
  }
  if ((unsigned)argc > 1 + pos_args.size()) {
    prog_usage();
    prog_error();
    cerr << "unrecognized arguments:";
    for (unsigned i = pos_args.size() + 1; i < (unsigned)argc; ++i) {
      cerr << " " << argv[i];
    }
    cerr << "\n";
    return 2;
  }

  fs::path starting_dir;
  // fs::absolute would throw fs::filesystem_error when given empty string
  if (argv[1][0] != '\0') {
    starting_dir = fs::absolute(argv[1]).lexically_normal();
    // fs::path::filename would be empty if there's a trailing separator, so
    // remove the trailing separator with parent_path
    if (!starting_dir.has_filename())
      starting_dir = starting_dir.parent_path();

    auto a = starting_dir.begin(), b = mount.begin();
    while (a != starting_dir.end() && b != mount.end() && *a == *b) {
      ++a;
      ++b;
    }
    if (b == mount.end()) {
      if (a != starting_dir.end())
        goto valid_directory;

      if (!recursive(starting_dir) &&
          std::distance(fs::directory_iterator(starting_dir), {}) == 1) {
        starting_dir = *fs::directory_iterator(starting_dir);
        goto valid_directory;
      }
    }
  }
  prog_error();
  cerr << "must be a subdirectory of /mnt [" << starting_dir.native() << "]\n";
  return 1;
valid_directory:

  if (recursive(starting_dir)) {
    prog_error();
    cerr << "recursive starting directory [" << starting_dir.native() << "]\n";
    return 1;
  }

  uid_t const root_uid = getpwnam("root")->pw_uid;
  gid_t gid = -1;
  {
    struct group const *const group = getgrnam(argv[2]);
    if (!group) {
      prog_error();
      cerr << "nonexistent group [" << argv[2] << "]\n";
      return 1;
    }
    gid = group->gr_gid;
  }

  if (!fs::is_directory(starting_dir)) {
    prog_error();
    cerr << "not a directory [" << starting_dir.native() << "]\n";
    return 1;
  }

  std::unordered_set<fs::path> visited;
  fs::path const canonical_starting_dir = fs::canonical(starting_dir);

  try {

    apply(fs::directory_entry(starting_dir), visited, 0, canonical_starting_dir,
          root_uid, gid);

    // whatever files inside the mount
    for (auto it = fs::recursive_directory_iterator(
             starting_dir, fs::directory_options::follow_directory_symlink |
                               fs::directory_options::skip_permission_denied);
         it != fs::recursive_directory_iterator(); ++it) {
      if (apply(*it, visited, it.depth(), canonical_starting_dir, root_uid,
                gid))
        it.disable_recursion_pending();
    }
  } catch (fs::filesystem_error const &e) {
    prog_error();
    cerr << e.what() << "\n";
    return 1;
  }
}
