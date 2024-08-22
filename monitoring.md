# Monitoring
Galaxy Europe uses the Telegraf InfluxDB Grafana (TIG) stack.

## Grafana
### Grafana OnCall
Is a Plugin and mobile app that lets you organize incident response management (IRM). You can create teams which organiue on-call shifts in calendars and add them to escalation chains so people who are on-call are notified e.g. by push message on their phones.
#### How to onboard a new user to OnCall
1. Add the user to the respective GitHub group, currently we have only one, that is called [admingrafana](https://github.com/orgs/usegalaxy-eu/teams/admingrafana). It is not visible and one of the org admins has to add the user.
2. Download the OnCall mobile app [iOS](https://apps.apple.com/de/app/grafana-oncall/id1669759048) or [Andriod](https://play.google.com/store/apps/details?id=com.grafana.oncall.prod&hl=en).
3. Verify if the user appears as `Admin` in `Organization Users` under `Administration → Users and Access → Users`. If not, the user can try to log out and in. 
4. Once you see them with Role `Admin` you can precede by adding them to the `GalaxyAdmins` team. You can find this under `Administration → Users and Access → Users`. Grab a coffee, it can take up to 30 min or even more until Grafana updates this in OnCall.
5. In the meantime, the user can connect the OnCall app, by opening the [IRM](https://stats.galaxyproject.eu/profile?tab=irm) tab in their Grafana profile. Scan the QR-code with your OnCall app, by selecting `sign in using QR code`. It is possible that you need to fully close and restart the app to make it work. Sometimes the scanner doesn't work directly.
6. Once the user is visible with the `Admin` role under `Organization Users` and is shown when you filter the `Users` table under `Alerts & IRM → OnCall → Users` by `Team` `GalaxyAdmins`, you can give them a shift in the [Google Calendar](https://calendar.google.com/calendar/embed?src=a1fcfef7e6458ceaeb48af57a5875025374525d282434fcfd714f3e38659d5df%40group.calendar.google.com&ctz=Europe%2FBerlin). Do that by using their Grafana `username` as event title. By this OnCall can match the calendar events to the individual user's shifts.
7. Now go to `Alerts & IRM → OnCall → Schedules`, click on `Admin Shifts` and check if you new user's shift is visible there. If not, click on `reload` and make sure the calendar is synced, the name is spelled correctly and the user has admin permissions and is shown in the OnCall team.
8. Now the user can set their default notifications in their profile in `Alerts & IRM → OnCall → Users` and set them to `push notifications` in order to use the mobile app.
9. You can test this by sending a test alert in `OnCall → Integrations → Admin Alerts` and `Send demo alert`.
