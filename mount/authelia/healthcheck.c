#include <ctype.h>      // for isgraph
#include <stdbool.h>    // for bool
#include <stdio.h>      // for perror, size_t, NULL, fputs, stderr, fclose
#include <stdlib.h>     // for exit, free, getenv, malloc, WEXITSTATUS, WIFE...
#include <string.h>     // for strlen, memcpy, strncmp, strndup
#include <sys/types.h>  // for ssize_t
#include <sys/wait.h>   // for waitpid
#include <unistd.h>     // for execlp, fork


#define ENV_NS "X_AUTHELIA_HEALTHCHECK"
#define ENV(name) ENV_NS "_" #name

char const *envs[] = {ENV_NS, ENV(SCHEME), ENV(HOST), ENV(PORT), ENV(PATH)};
char const *defaults[] = {NULL, "http", "localhost", "9091", NULL};

#define NUM_ENV (sizeof(envs) / sizeof(envs[0]))


int main(int argc, char* _[])
{
      if (argc > 1) {
            fputs("Should be run without arguments", stderr);
            goto exit;
      }

      char *line = NULL;
      size_t n;
      char *vals[NUM_ENV] = {};
      bool allocated[NUM_ENV] = {};

      FILE *const f = fopen("/app/.healthcheck.env", "r");
      if (!f) {
            perror("Error reading healthcheck env file");
            goto exit;
      }

      ssize_t l;
      while ((l = getline(&line, &n, f)) != -1) {
            if (l < sizeof(ENV_NS))
                  continue;

            for (size_t i = 0; i < NUM_ENV; ++i) {
                  size_t const env_len = strlen(envs[i]);
                  if (!(l >= env_len + 1 && !strncmp(envs[i], line, env_len)
                        && line[env_len] == '='))
                        continue;

                  while (!isgraph(line[l - 1]))
                        --l;

                  if (allocated[i])
                        free(vals[i]);

                  vals[i] = NULL;
                  if ((allocated[i] = l > env_len + 1) &&
                       !(vals[i] = strndup(line + env_len + 1,
                                           l - (env_len + 1)))) {
                        perror("Couldn't duplicate string");
                        goto close_f;
                  }
                  break;
            }
      }

close_f:
      if (fclose(f)) {
            fputs("Couldn't close healthcheck env file\n", stderr);
            goto exit;
      }

      for (size_t i = 0; i < NUM_ENV; ++i) {
            if (allocated[i]) 
                  continue;

            vals[i] = getenv(envs[i]);

            if (!vals[i] || !vals[i][0])
                  vals[i] = (char *)defaults[i];
      }

      if (!vals[0]) {
            goto exit;
      }

      char const* parts[] = {
            vals[1],
            "://",
            vals[2],
            ":",
            vals[3],
            vals[4],
            "/api/health"
      };
      size_t const num_parts = sizeof(parts) / sizeof(parts[0]);
      size_t url_len = 1;
      for (size_t i = 0; i < num_parts; ++i) {
            url_len += parts[i] ? strlen(parts[i]) - 1 : 0;
      }
      char *const c = malloc(url_len);
      if (!c) {
            goto exit;
      }
      char *cur = c;
      for (size_t i = 0; i < num_parts; ++i) {
            if (!parts[i])
                  continue;

            size_t const part_len = strlen(parts[i]);
            memcpy(cur, parts[i], part_len);
            cur += part_len;
      }
      *cur = '\0';
      fflush(stderr);

      int const pid = fork();
      if (pid == -1) {
            perror("Error forking");
            goto exit;
      }
      if (!pid) {
            execlp("wget",
                   "wget", "-q", "--tries", "1", "--spider", c, NULL);
            perror("Error executing wget");
            goto exit;
      }
      int wstatus;
      if (waitpid(pid, &wstatus, 0) == -1) {
            perror("Error waiting for child wget process");
            goto exit;
      }
      exit((bool)wstatus);

exit:
      return 1;
}
