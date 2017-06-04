import os
import requests
import time
import json
import sys
import subprocess
import datetime
import getopt


ROOT_PATH = os.getcwd()


class TwitchRecorder:
    def __init__(self):
        self.client_id = 'jzkbprff40iqj646a697cyrvl0zt2m6'  # use this, don't change
        self.oauth_token = 'j6ncsmg4mrgs7ye6gdpsqhin9c5o9k'  # streamlink --twitch-oauth-authenticate
        self.ffmpeg_path = ROOT_PATH + '/ffmpeg/bin/ffmpeg.exe'
        self.refresh = 60.0
        self.root_path = ROOT_PATH + '/twitch_videos'
        self.username = 'a1101x'
        self.quality = 'best'
        self.processed_path = os.path.join(self.root_path, 'processed',
                                           self.username)
        self.recorded_path = os.path.join(self.root_path, 'recorded',
                                          self.username)

    def check_user(self):
        url = 'https://api.twitch.tv/kraken/streams/' + self.username
        info = None
        status = 3  # 0: online, 1: offline, 2: not found, 3: error

        try:
            r = requests.get(url, headers={'Client-ID': self.client_id},
                             timeout=15)
            r.raise_for_status()
            info = r.json()

            if info['stream'] is None:
                status = 1
            else:
                status = 0

        except requests.exceptions.RequestException as e:

            if e.response:
                if e.response.reason == 'Not Found' or e.response.reason == \
                        'Unprocessable Entity':
                    status = 2

        return status, info

    def checker(self):
        while True:
            status, info = self.check_user()

            if status == 2:
                print('Username not found. Invalid username or typo.')
                time.sleep(self.refresh)
            elif status == 3:
                print(datetime.datetime.now().strftime('%Hh%Mm%Ss'), ' ',
                      'unexpected error. will try again in 5 minutes.')
                time.sleep(600)
            elif status == 1:
                print(self.username, 'currently offline, checking again in',
                      self.refresh, 'seconds.')
                time.sleep(self.refresh)
            elif status == 0:
                print(self.username, 'online. Stream recording in session.')
                filename = self.username + ' - ' + datetime.datetime.now().\
                    strftime('%Y-%m-%d %Hh%Mm%Ss') + ' - ' + (info['stream']).\
                    get('channel').get('status') + '.mp4'

                filename = ''.join(x for x in filename if x.isalnum() or x in
                                   [' ', '-', '_', '.'])
                recorded_filename = os.path.join(self.recorded_path, filename)
                subprocess.call(
                    ['streamlink', '--twitch-oauth-token', self.oauth_token,
                     'twitch.tv/' + self.username, self.quality,
                     '-o', recorded_filename])
                print('Recording stream is done. Fixing video file.')

                if os.path.exists(recorded_filename) is True:
                    try:
                        subprocess.call(
                            [self.ffmpeg_path, '-err_detect', 'ignore_err',
                             '-i', recorded_filename, '-c', 'copy',
                             os.path.join(self.processed_path, filename)])
                        os.remove(recorded_filename)
                    except Exception as e:
                        print(e)
                else:
                    print('Skip fixing. File not found.')

                print('Fixing is done. Going back to checking..')
                time.sleep(self.refresh)

    def run(self):
        if os.path.isdir(self.recorded_path) is False:
            os.makedirs(self.recorded_path)

        if os.path.isdir(self.processed_path) is False:
            os.makedirs(self.processed_path)

        if self.refresh < 15:
            print('Check interval should not be lower than 15 seconds.')
            self.refresh = 15
            print('System set check interval to 15 seconds.')

        try:
            video_list = [f for f in os.listdir(self.recorded_path) if
                          os.path.isfile(os.path.join(self.recorded_path, f))]

            if len(video_list) > 0:
                print('Fixing previously recorded files.')

            for f in video_list:
                recorded_filename = os.path.join(self.recorded_path, f)
                print('Fixing ' + recorded_filename + '.')

                try:
                    subprocess.call(
                        [self.ffmpeg_path, '-err_detect', 'ignore_err', '-i',
                         recorded_filename, '-c', 'copy',
                         os.path.join(self.processed_path, f)])
                    os.remove(recorded_filename)
                except Exception as e:
                    print(e)

        except Exception as e:
            print(e)

        print('Checking for', self.username, 'every', self.refresh,
              'seconds. Record with', self.quality, 'quality.')
        self.checker()


def main(argv):
    twitch_recorder = TwitchRecorder()
    usage_message = 'twitch-recorder.py -u <username> -q <quality>'

    try:
        opts, args = getopt.getopt(argv, 'hu:q:', ['username=', 'quality='])
    except getopt.GetoptError:
        print(usage_message)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usage_message)
            sys.exit()
        elif opt in ('-u', '--username'):
            twitch_recorder.username = arg
        elif opt in ('-q', '--quality'):
            twitch_recorder.quality = arg

    twitch_recorder.run()


if __name__ == '__main__':
    main(sys.argv[1:])


# python recorder.py --user=username
