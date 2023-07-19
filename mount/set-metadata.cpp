#include <array>
#include <cerrno>
#include <filesystem>
#include <iostream>
#include <iterator>
#include <optional>
#include <string>

#include <grp.h>
#include <pwd.h>
#include <unistd.h>

namespace fs = std::filesystem;
using std::cerr;
using namespace std::string_literals;

static std::optional<std::string> prog;
constexpr std::array pos_args = {"MOUNT", "GROUP"};

void prog_error() { cerr << *prog << ": error: "; }

void prog_usage() {
  cerr << "usage: " << *prog << " [-h|--help]";
  for (const auto &arg : pos_args) {
    cerr << " " << arg;
  }
  cerr << "\n";
}

int main(int argc, char *argv[]) {

  prog = fs::path(argv[0]).filename();

  for (unsigned i = 1; i < argc; ++i) {
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

  if (argc < 1 + pos_args.size()) {
    prog_usage();
    prog_error();
    cerr << "the following arguments are required:";
    for (unsigned i = argc - 1; i < pos_args.size(); ++i)
      cerr << " " << pos_args[i];
    cerr << "\n";
    return 2;
  }
  if (argc > 1 + pos_args.size()) {
    prog_usage();
    prog_error();
    cerr << "unrecognized arguments:";
    for (unsigned i = pos_args.size() + 1; i < argc; ++i) {
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

    fs::path const relative_path = starting_dir.relative_path();
    auto const relative_path_begin = relative_path.begin();

    if (*relative_path_begin == "mnt") {
      unsigned const num_components =
          std::distance(relative_path_begin, relative_path.end());

      if (num_components > 1)
        goto valid_directory;

      if (num_components == 1 &&
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

  try {

    // do the mount directory itself
    if (chown(starting_dir.c_str(), root_uid, gid))
      throw fs::filesystem_error("cannot set ownership", starting_dir,
                                 {errno, std::system_category()});
    fs::perms const original_perms = fs::status(starting_dir).permissions();
    fs::perms perms = original_perms & fs::perms::owner_all;

    if (static_cast<bool>(perms & fs::perms::owner_read))
      perms |= fs::perms::group_read;
    if (static_cast<bool>(perms & fs::perms::owner_exec))
      perms |= fs::perms::group_exec | fs::perms::others_exec;

    if (perms != original_perms)
      fs::permissions(starting_dir, perms);

    // whatever files inside the mount
    for (auto it = fs::recursive_directory_iterator(
             starting_dir, fs::directory_options::skip_permission_denied);
         it != fs::recursive_directory_iterator(); ++it) {

      if (it->is_symlink())
        continue;

      fs::path const &path = it->path(), filename = path.filename();

      if (chown(path.c_str(), root_uid, gid))
        throw fs::filesystem_error("cannot set ownership", path,
                                   {errno, std::system_category()});

      fs::perms const original_perms = it->status().permissions();
      fs::perms perms = original_perms & fs::perms::owner_all;

      if (it->is_directory() && filename == ".git")
        it.disable_recursion_pending();
      else {

        if (it->is_regular_file() && filename.extension() == ".sh")
          perms |= fs::perms::owner_exec;

        if (static_cast<bool>(perms & fs::perms::owner_read)) {
          perms |= fs::perms::group_read;
          fs::path const relative_path = path.lexically_relative(starting_dir);
          if (std::distance(relative_path.begin(), relative_path.end()) > 1 &&
              it->is_regular_file()) {
            perms |= fs::perms::others_read;
          }
        }
        if (static_cast<bool>(perms & fs::perms::owner_exec))
          perms |= fs::perms::group_exec | fs::perms::others_exec;
      }
      if (perms != original_perms)
        fs::permissions(path, perms);
    }
  } catch (fs::filesystem_error const &e) {
    prog_error();
    cerr << e.what() << "\n";
    return 1;
  }
}
