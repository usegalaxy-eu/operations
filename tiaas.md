# Approving TIaaS Requests

1. Go to the [TIaaS trainings board](https://usegalaxy.eu/tiaas/admin/training/training/).
2. Filter for [unprosessed](https://usegalaxy.eu/tiaas/admin/training/training/?processed__exact=UN)
3. Click on the training identifier to open the training overview
4. Check the description and estimate if it is a valid training request
5. Check the dates. If the request is on month we do not approve it.
6. Check in the [calendar](https://usegalaxy.eu/tiaas/calendar/) that there are not many trainings at the same time
7. Change the status of the request: at the bottom, change `Processed` to `Approved` and save
8. Check in the [calendar](https://usegalaxy.eu/tiaas/calendar/) that the training has been booked.
8. Send the following email to the user. You will find all needed infromation on the training page.  Don't forget to but galaxy mail in cc.


```
Subject: UseGalaxy.eu TIaaS Request: Approved, Training ID: **Training identifier**
```

```
Dear **Name**,

Thanks for submitting your TIaaS request.

TIaaS provides a private queue for trainings in addition to the regular one, which should make your jobs run a bit faster. To make use of it, we have created a training group for you that is accessible at

https://usegalaxy.eu/join-training/**Training identifier**/

Please ask your users to go to that URL during your training (from **202X-XX-XX** to **202X-XX-XX**). Once it is over, the link will not be usable anymore but the users can still access their data at usegalaxy.eu.

Queue Status: If you find yourself wondering where your students are during the training, you can use the queue status page to see which jobs are being run by people in your training: https://usegalaxy.eu/join-training/**Training identifier**/status

Storage: We recommend to use Galaxy's short-term storage during the training. This will help us in cleaning up unused data and offer Galaxy as a more sustainable service. For more information please consult our storage page.

Support: If during the workshop you experience issues with the server, you can ask for support in the Galaxy Europe Gitter channel: https://matrix.to/#/#usegalaxy-eu_Lobby:gitter.im or via email: contact@usegalaxy.eu

Please keep in mind that usegalaxy.eu is a free service and we do not charge any fees to our users. We do our best to maintain a highly available and reliable cluster, but there may still be outages we cannot control. We would like to ask you to be lenient in such cases. You can view our service status here: https://status.galaxyproject.org/

In case of prolonged unexpected server outage, you could consider using one of the other usegalaxy.* instances. You can find them on the status page mentioned above. Keep in mind that your registered TIaaS session with the dashboard and separate queue is only available on usegalaxy.eu.

Workshop Feedback: When your workshop is over, if you used GTN materials, please let us know how it went on the workshop feedback issue: https://github.com/galaxyproject/training-material/issues/1452

TIaaS Feedback: We encourage you to send us a short review sharing your experience, tips for other instructors,… that we will publish in https://galaxyproject.eu/news?tag=TIaaS. Your feedback is very valuable to keep this service up and running for free.

We really appreciate your support. Thank you very much for using Galaxy and don’t hesitate to contact us if you have any questions!

Kind regards,
**Your Name**

```
9. Before sending check if the links are working and you changed all the dates and identifier

---

# FAQ

Question | Answer
--- | ---

What is the format for the date? | `YYYY-mm-dd`
