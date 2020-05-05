# Approving TIaaS Requests

1. Go to the [unprocessed trainings](https://usegalaxy.eu/tiaas/admin/training/training/?processed__exact=UN).
2. Click on one training: this brings you to the edit-tiaas-request page.
3. Estimate the resources:
    - Get the [individual resources for each tool](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/files/galaxy/dynamic_rules/usegalaxy/tool_destinations.yaml) needed in the training. If a tool is not on the list, you can assume `{mem: 4, cores: 1}`.
    - Get the max_resources based on the max mem and max cores for all the requested tools.
    - estimated_resources = max_resources * (#users + 2)
4. Change the status of the request: at the bottom, change `Processed` to `Approved`.
5. Save the changes.
6. Script for the resource allocation:
    - Clone https://github.com/usegalaxy-eu/vgcn-infrastructure
    - Go into `vgcn-infrastructure`, and run `./add-training.sh` with the left parameters:

   ```
    Usage:
      ./add-training.sh <training-identifier> <vm-size (e.g. c.c32m240)> <vm-count> <start in YYYY-mm-dd> <end in YYYY-mm-dd> [-- donotautocommitpush]
    ```    
    - The script will add an entry to [`resources.yaml`](https://github.com/usegalaxy-eu/vgcn-infrastructure/blob/master/resources.yaml) with the information for the training.
    - If the option `donotautocommitpush` was not used, the script will commit and push.
    - A template email will be printed as a result of the script.
    - **NOTE**: There are 9 training nodes. If two trainings overlap, the number of total nodes shouldn't exceed 9. 
    
7. Check in the [calendar](https://usegalaxy.eu/tiaas/calendar/) that the training has been booked.
8. Send the email to the user.

### What happens in the background

- The next time the galaxy playbook runs, it deploys the tiaas training. Then the URL becomes active.
- Whenever `todays_date >= start date`, vgcn-infrastructure will automatically **try** and launch the VM.

---

# FAQ

Question | Answer
--- | ---
What if there are multiple trainings? | It has not happened yet. If it does, it is with long-running trainings and we usually give them fewer / smaller machines.
What is the recommended machine? | `c.c32m240`, generally used for training, so no changes to the main queue needed.
What is the format for the date? | `YYYY-mm-dd`
How many machines can be assigned? | There is a maximum of __8__ machines.
How do I estimate the resources accurately? | It's hard to estimate the number correctly without more information that isn't so easy to collect. Usually there's no information about the time limitations they have, maybe they expect a step to run in 1 minute, but we don't know that. We don't know either if they'll run a dataset collection.
