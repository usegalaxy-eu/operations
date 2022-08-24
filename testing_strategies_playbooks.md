# Testing Strategies for Playbooks
Generally Ansible is a model of desired-state, so it automatically ensures that packages are installed etc.
If you want to be sure that something works, the best approach is to write this desired state into your playbook.

## Check Mode
The ``--check`` mode is helpful for a basic testing before actual deployment as it estimates if there will be any changes necessary to bring the system to the desired state.
To run scripts and commands despite  
the `--check` flag, it is possible to add
```yml
check_mode: no
```
to your task.
However this is limited, because some tasks depend on earlier changes and these would not be applied in `--check` mode and services do not actually run.
## Useful Modules
1. [`ansible.builtin.wait_for`](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/wait_for_module.html)  
This module is can allow you to wait for a specific **Port** or a **File** to be available or not on the system or using **regex** to verify that a certain string is present. The docs contain multiple helpful examples. 
2. URI Module to make sure a web service runs  
```yml
tasks:

  - action: uri url=https://www.example.com return_content=yes
    register: webpage

  - fail:
      msg: 'service is not happy'
    when: "'AWESOME' not in webpage.content"
```
3. [ansible.builtin.script](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/script_module.html)  
When scripts return a non-zero return code, the task will fail, too.
4. [ansible.builtin.assert](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/assert_module.html)  
Asserts all kind of things :)

Generally said: It is better to declare a desired state in your playbook than to test it.

## Testing Lifecycle
Ansible suggests a workflow like the following:
```
- Use the same playbook all the time with embedded tests in development
- Use the playbook to deploy to a staging environment (with the same playbooks) that simulates production
- Run an integration test battery written by your QA team against staging
- Deploy to production, with the same integrated tests.
```
Additionally some QA Batteries could be included:
## Integrated Testing
By using `pre_tasks` and `post_tasks`, it is possible to include some testing roles before integrate a machine in production environment. With the `delegate_to` parameter, it is possible to include test that run on a dedicated test-server against that machine.  
As next step to achieve Continuous Deployment, Ansible suggests to run everything against a staging environment first and only if that succeeds against the production environment.

## Conclusion

General health checks are the preferred way, additional, specific tests should not be needed in playbooks in deployment, because Ansible is designed to fail fast and bring errors to the top.  
The focus should be on QA application testing and **not** on infrastructure testing.
