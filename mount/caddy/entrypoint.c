#define _GNU_SOURCE

#include <assert.h>    // for assert
#include <stdbool.h>   // for false
#include <stdio.h>     // for perror, fputs, stderr, fclose, ferror, fflush
#include <stdlib.h>    // for exit, malloc, secure_getenv
#include <string.h>    // for memcpy, strlen, strstr
#include <unistd.h>    // for execvp


#define BINARY "caddy"


int main(int argc, char* argv[])
{
      int stage_successes = 0;
      if (argc < 2) {
            fprintf(stderr, "Usage: %s mta_sts_file [ARGS...]\n", argv[0]);
            goto exit;
      }

      FILE *const f = fopen(argv[1], "a");
      if (!f) {
            perror("Error reading config file");
            goto exit;
      }
      char const *const subdomain = secure_getenv("MX_SUBDOMAIN");
      if (!subdomain || !subdomain[0]) {
            fputs("ERROR: $MX_SUBDOMAIN is missing or empty\n", stderr);
            goto close_f;
      }
      char const *const domain = secure_getenv("DOMAIN");
      if (!domain || !domain[0]) {
            fputs("ERROR: $DOMAIN is missing or empty\n", stderr);
            goto close_f;
      }

      if (fprintf(f, "mx: %s.%s\n", subdomain, domain) == -1) {
            fputs("Error appending to file\n", stderr);
            goto close_f;
      }

      ++stage_successes;

close_f:
      if (fclose(f) == -1) {
            fputs("Error closing file\n", stderr);
            goto exit;
      }

      if (!stage_successes) {
            goto exit;
      }

      char const **const exec_args = malloc(argc * sizeof(char *));
      if (!exec_args) {
            perror("Error allocating memory for exec args");
            goto exit;
      }
      exec_args[0] = BINARY;
      memcpy(exec_args + 1, argv + 2, (argc - 2) * sizeof(char *));
      exec_args[argc] = NULL;
      fflush(stderr);
      execvp(BINARY, (char *const *)exec_args);
      perror("Error executing " BINARY);

exit:
      exit(1);
}
