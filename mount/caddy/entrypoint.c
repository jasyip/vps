#include <stdio.h>     // for perror, fputs, stderr, fclose, fflush
#include <stdlib.h>    // for exit, getenv
#include <string.h>    // for memmove, strlen, strstr
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
      char const *const subdomain = getenv("MX_SUBDOMAIN");
      if (!subdomain || !subdomain[0]) {
            fputs("ERROR: $MX_SUBDOMAIN is missing or empty\n", stderr);
            goto close_f;
      }
      char const *const domain = getenv("DOMAIN");
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

      fflush(stderr);
      argv[0] = BINARY;
      memmove(argv + 1, argv + 2, (argc - 1) * sizeof(char *));
      execvp(BINARY, argv);
      perror("Error executing " BINARY);

exit:
      exit(1);
}
