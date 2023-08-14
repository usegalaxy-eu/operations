# Interactive Tools (VREs)

It is possible to run tools in Galaxy that are by nature interactive. The most prominent examples of this are most likely Jupyter Notebook and RStudio.
But there are other interactive use cases like advanced (dependent on a server) visualisations, or entire Desktop applications that need an X(like)-server.
Those environments are usually called VREs - Virtual Research Environments.

Galaxy has support for [Interactive Environments](https://doi.org/10.1371/journal.pcbi.1005425) since 2016 and restructured the initial implementation somewhere around 2019.
"Interactive Tools" (ITs), as we call it today, are internally be based on the tool framework in Galaxy. They are ordinary Galaxy tools, with a few more metadata attributes (like exposed port) and
the requirement to run them in a container.

We are running ITs on EU and have some special nodes dedicated to them. We also have this special subdomain: https://live.usegalaxy.eu (not all ITs are listed there).

In general, we welcome contributions and new ITs to be deployed on the European Galaxy server.
Here are the steps you need to follow to get your IT deployed.

1. Crate a public GitHub repository in which you publish your Docker container.

   It should have:
    - README
    - License
    - CI that builds and pushed your container
   
   Here are a few example repositories:
    - Jupyter-based example: https://github.com/usegalaxy-eu/docker-divand
    - Desktop-App based example: https://github.com/usegalaxy-eu/docker-qgis
3. Create the Galaxy Tool description and submit it as PR to the [EU Galaxy deployment for review](https://github.com/usegalaxy-eu/galaxy/tree/release_23.0_europe/tools/interactive).
   Note: We might ask you to add your IT to the [upstream Galaxy repository](https://github.com/galaxyproject/galaxy) repo, where it ideally should be deposited and maintained.
5. Enable your IT in our daily deployment by:
   - [adding it to the IT tool list that will be loaded](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/templates/galaxy/config/tool_conf.xml.j2#L530)
   - [define the number of CPUs and memory needed for your IT](https://github.com/usegalaxy-eu/infrastructure-playbook/blob/master/files/galaxy/tpv/interactive_tools.yml#L44)
6. Optional: If you want to have your IT listed at the special https://live.usegalaxy.eu site, add an [entry to the website](https://github.com/usegalaxy-eu/website/blob/master/index-live.md?plain=1#L87).
