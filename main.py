import datetime
import time

import dateutil.parser
import fitbit
import pytz

import gather_keys_oauth2 as Oauth2
import secrets


def auth():
    server = Oauth2.OAuth2Server(secrets.CLIENT_ID, secrets.CLIENT_SECRET)
    server.browser_authorize()
    ACCESS_TOKEN = str(server.fitbit.client.session.token['access_token'])
    REFRESH_TOKEN = str(server.fitbit.client.session.token['refresh_token'])
    auth2_client = fitbit.Fitbit(secrets.CLIENT_ID, secrets.CLIENT_SECRET, oauth2=True, access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN, system=fitbit.Fitbit.METRIC)
    return auth2_client


class User:
    def __init__(self):
        self.client = auth()
        self._devices = self.client.get_devices()
        self._alarms = self.client.get_alarms(self.device_id)
        if len(self._alarms['trackerAlarms']) > 1:
            raise ValueError

        self._profile = self.client.user_profile_get()
        self.timezone = pytz.timezone(self._profile['user']['timezone'])
        self._sleep_goal = self.client._resource_goal('sleep')

        self._sleep = self.client.sleep()
        self.sleep_target = self._sleep_goal['goal']['minDuration']
        self.alarm_id = self._alarms['trackerAlarms'][0]['alarmId']

    @property
    def sleep_time(self):
        self._sleep = self.client.sleep()
        return self._sleep['summary']['totalMinutesAsleep']

    @property
    def device_id(self):
        return self._devices[0]['id']

    @property
    def now(self):
        return self.timezone.localize(datetime.datetime.now())

    def update_alarm(self, new_alarm_time):
        self.client.update_alarm(
            self.device_id, self.alarm_id, new_alarm_time, week_days=self.client.WEEK_DAYS, snooze_count=1, snooze_length=1, label="NexusWake", )

    @property
    def is_awake(self):
        self._sleep = self.client.sleep()

        if len(self._sleep['sleep']) == 0:
            return True

        wake_time = dateutil.parser.parse(self._sleep['sleep'][-1]['endTime'])
        awake_for = self.now - self.timezone.localize(wake_time)
        print("Awake for", awake_for)
        return awake_for.total_seconds() > 0


def main():
    user = User()

    while True:

        print("Wakeup...", end="")
        if user.is_awake:
            print(user._sleep)
            print("User Awake, bye.")
        else:
            print()
            sleep_left = datetime.timedelta(minutes=user.sleep_target - user.sleep_time)
            new_alarm_time = user.now + sleep_left
            print(f"New alarm {new_alarm_time}")
            user.update_alarm(new_alarm_time)
            print("Sleep(5 min)")
        time.sleep(5 * 60)


if __name__ == '__main__':
    main()
