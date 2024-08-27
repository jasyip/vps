#include <stdbool.h>    // for bool
#include <stdio.h>      // for perror
#include <sys/types.h>  // for pid_t
#include <sys/wait.h>   // for waitpid
#include <unistd.h>     // for execvp, fork

int main(int _, char *argv[])
{
      pid_t const pid = fork();
      if (pid == -1) {
            perror("Error forking");
            goto exit;
      }
      if (!pid) {
            argv[0] = "wget";
            execvp("wget", argv);
            perror("Error executing wget");
            goto exit;
      }
      int wstatus;
      if (waitpid(pid, &wstatus, 0) == -1) {
            perror("Error waiting for child wget process");
            goto exit;
      }
      return (bool)wstatus;

exit:
      return 1;
}
