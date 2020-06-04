# gmail-email-scheduler

Simple Python script for sending GMail drafts at scheduled times. This is a bare-bones implementation, if you want to use this you'll have to set up your own environment - a virtual machine in AWS that runs continuously, or perhaps a Raspberry Pi that hosts the script.

**You must have technical knowledge in order to set the script up, this isn't designed to be user-friendly.**

How this works:
* The script periodically goes through all saved drafts on a GMail account.
* For every draft, check the `schedule.csv` file to see if that e-mail is scheduled to be sent at a particular time.
* If a draft is scheduled to be sent and the time is in the past, send the e-mail.

### Setup

* Install Python 3 ( tested with Python 3.5.1), including `pip`.
* Install developer headers (`sudo apt-get install python3-dev`).
* Follow the steps described in [this Google Developer article](https://developers.google.com/gmail/api/quickstart/python) in order to set up your credentials file (`credentials.json`).
* Install `dateparser` for Python (`pip install dateparser`).

### How to use the script

* After performing the steps in the previous section, you should have a new file called `credentials.json` in your project folder.
* Replace instances of `Europe/Bucharest` in the script with your desired timezones.
* Start the script and leave it running forever.
* The first time it runs, you'll need to authorize access it by logging into Google and following the wizard.
* Create the draft you want to schedule.
* Add the draft to `schedule.csv` (lines are separated using `|`, so add lines such as `Draft title|12/25/2020 15:00`).

### Want to run in AWS?

These were the steps I took to set up an EC2 instance to run the script continuously:
* Created a `t3a.nano` instance with a persistent 8 GB EBS storage using the Linux 2 AMI. You don't need high performance for the script, so I went with the cheapest option.
* SSH-ed into the virtual machine.
* Installed Python 3 and all of the dependencies mentioned above in the "Setup" section.
* Installed requirements for setting up Dropbox on the machine (`yum install mesa-libGL`).
* Installed a headless Dropbox instance as described on the [official website](https://www.dropbox.com/install-linux) using `cd ~ && wget -O - "https://www.dropbox.com/download?plat=lnx.x86_64" | tar xzf`
* Started the Dropbox daemon from `~/.dropbox-dist/dropboxd &`. Used the provided link in order to create / login into the Dropbox account on a separate machine (one with a web browser).
* Ensured the path to the schedule is correct in `application.py`.
* Copied the `token.pickle` and `credentials.json` files from my local machine to the EC2 (after running the script locally first).
* Started the application using `python3 ~/gmail-scheduler/application.py &`.

### Differences from Google's scheduling feature

The advantage of Google's solution is that it's beautifully integrated with the GMail clients and it's very easy to use and intuitive for non-technical users. The only advantage of my solution (and why I still use it) is that you can continue editing drafts even after scheduling them to be sent (once you mark an e-mail as scheduled in Google, you can't edit it without removing the schedule).
