# RASA notes

Please check out the official [rasa website](https://rasa.com/docs/) for more detailed docs. The following is just a gist for quick reference.

## Model configuration

The [model configuration](https://rasa.com/docs/rasa/model-configuration) happens in `config.yml`.

## Domain

The bot's domain is "the universe the bot operates in" and is configured in `domain.yml`. This includes the list of intents, responses, actions, etc.

## Endpoints

The `endpoints.yml` file specifies the [tracker store](https://rasa.com/docs/rasa/tracker-stores/) and [event brokers](https://rasa.com/docs/rasa/event-brokers) respectively.

## NLU

The `data/nlu.yml` file contains training data to extract structured information from user messages.

## Rules

The `data/rules.yml` file is used to train the bots dialogue management model (short pieces of conversation that shoud follow the same path).

## Stories

The `data/stories.yml` file is used to train the bots dialogue management as well (to generalize unseen conversation paths).

## General terms

  - Intent: What is the user intending to ask about?
  - Entity: What are the important pieces of information in the user's query?
  - Story: What is the possible way the conversation can go?
  - Action: What action should the bot take upon a specific request?

# Directory structure

The `deploy/openshift-pipelines/generic` directory contains items that are used by all pipelines. For example:

  - EventListener: Connects the TriggerBinding to the TriggerTemplate. Creates a bunch of resources in the project (`$ oc get all -l app.kubernetes.io/managed-by=EventListener`).
  - RoleBinding: Gives the `github-tekton-sa` SerivceAccount admin access in the dusbot project.
  - ServiceAccount: Service Account used to clone code from the private dusbot repostiory (will probably obsolete when the repo is made public).
  - Task (awscli): Interacts with S3 to upload and download the latest rasa model.
  - Task (control-deployment-rollout): Used to control the DUSBot deployment.
  - Task (rasa): Controls the rasa cli.
  - Task (update-deployment): Patches the DUSBot deployment.
  - Task (update-github-pull-request): Used to comment on GitHub pull requests.

The `deploy/openshift-pipelines/deploy_dusbot`, `deploy/openshift-pipelines/build_dusbot` and `deploy/openshift-pipelines/validate_pull_request` directories contain items related to individual pipelines.

  - Pipeline: Describes the actual steps taken when deploying DUSBot.
  - PersistentVolumeClaim: Provides storage that is shared between Pipeline steps.
  - TriggerBinding: Identifies which fields are to be extracted from the webhook JSON payload to be presented to the TriggerTemplate.
  - TriggerTempalte: Connects the parameters defined in the TriggerBinding with a PipelineRun.

# Local development with podman

In case you don't want to use OpenShift Pipelines for CI/CD, you can test and deploy the bot locally with Podman.

## Action server

Start the [action server](https://rasa.com/docs/action-server).

```
$ podman pod create -n rasapod
```
```
$ chown -R 1000:1000 *
```
The `CRYPTOCOMPARE_APIKEY` environment variable should create a [cryptocompare api key](https://www.cryptocompare.com/coins/guides/how-to-use-our-api/) in order to test one of the bot's functionalities.
```
$ podman run \
	-d \
	-v ./actions:/app/actions:Z \
	--name action-server \
	--user 1000 \
	--pod rasapod \
	-e CRYPTOCOMPARE_APIKEY=foo \
	docker.io/rasa/rasa-sdk:2.1.2
```
```
$ podman logs action-server
2020-11-26 09:03:29 INFO     rasa_sdk.endpoint  - Starting action endpoint server...
2020-11-26 09:03:29 INFO     rasa_sdk.executor  - Registered function for 'action_tell_joke'.
2020-11-26 09:03:29 INFO     rasa_sdk.endpoint  - Action endpoint is up and running on http://localhost:5055
```

## Training the model
After changing the code, it might make sense to restart the action server before training so that it picks up potential new actions that have been added (`actions/`).

```
$ podman restart action-server
```
```
$ podman run \
	-it \
	--rm \
	-v ./:/app:Z \
	--user 1000 \
	--pod rasapod \
	docker.io/rasa/rasa:2.1.0-full train --fixed-model-name dusbot
```

## Interactive training data generation

You can also [interactively](https://rasa.com/docs/rasa/writing-stories/#using-interactive-learning) modify the training data. 
```
$ podman run \
	-it \
	--rm \
	-v ./:/app:Z \
	--user 1000 \
	--pod rasapod \
	docker.io/rasa/rasa:2.1.0-full interactive core -d domain.yml -m models -c config.yml --stories data
```

## Data validation

```
$ podman run \
	-it \
	--rm \
	-v ./:/app:Z \
	--user 1000 \
	--pod rasapod \
	docker.io/rasa/rasa:2.1.0-full data validate stories --fail-on-warnings --max-history 5
```

## Testing
```
$ podman run \
	-it \
	--rm \
	-v ./:/app:Z \
	--user 1000 \
	--pod rasapod \
	docker.io/rasa/rasa:2.1.0-full test --fail-on-prediction-errors
```

## Local interaction

You can interact with the bot locally as well.

```
$ podman run \
	-it \
	--rm \
	-v ./:/app:Z \
	--user 1000 \
	--pod rasapod \
	docker.io/rasa/rasa:2.1.0-full shell
```

# OpenShift Container Platform

In order to train the model, you'll need a CPU with Advanced Vector Extension (avx) [support](https://forum.rasa.com/t/illegal-instruction-core-dumped/30516/6).

## Tested environment

- Red Hat OpenShift Container Platform 4.6 running on bare metal
- Red Hat OpenShift Pipelines Operator version 1.2.2
- GitHub
- Google Hangouts Chat (business version)

## Setup development project

This project will execute pipelines and, as a result, train the model, build container images and deploy them to the test and prod namespaces.

```
$ oc new-project dusbot-dev
```
```
$ oc -n dusbot-dev apply -f deploy/openshift-pipelines/generic/
```
```
$ oc -n dusbot-dev apply -f deploy/openshift-pipelines/validate_pull_request/
```
```
$ oc -n dusbot-dev apply -f deploy/openshift-pipelines/deploy_dusbot/
```
```
$ oc -n dusbot-dev get po,svc
NAME                                           READY   STATUS    RESTARTS   AGE
pod/el-dusbot-eventlistener-6b7ff58d59-trfbw   1/1     Running   0          2m3s

NAME                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
service/el-dusbot-eventlistener   ClusterIP   172.30.186.138   <none>        8080/TCP   2m5s
```
```
$ oc -n dusbot-dev expose service/el-dusbot-eventlistener
```
```
$ oc -n dusbot-dev get route
NAME                      HOST/PORT                                                    PATH   SERVICES                  PORT            TERMINATION   WILDCARD
el-dusbot-eventlistener   el-dusbot-eventlistener-dusbot-dev.apps.ocp01.redhat.works          el-dusbot-eventlistener   http-listener                 None
```
```
$ curl http://el-dusbot-eventlistener-dusbot-dev.apps.ocp01.redhat.works
{"eventListener":"dusbot-eventlistener","namespace":"dusbot-dev","eventID":"rgvdk"}
```

Configure two GitHub [web hooks](https://github.com/koep/dusbot/settings/hooks) that point to the above route.

- One Webhook that is triggered on `pull_request` events.
- One Webhook that is triggered on `push` events.

Create two branch [protection rules](https://github.com/koep/dusbot/settings/branch_protection_rules/).

- Test:
    - Require status checks to pass before merging.
	- Require branches to be up to date before merging, sest-pull-request.
- Main:
    - No additional configuration.

Build the commit status tracker image as described in the [docs](https://github.com/tektoncd/experimental/tree/master/commit-status-tracker). The code is a git submodule in this repository and can be found in `deploy/experimental`. This component is used to populate the Tekton pipeline status to a given GitHub Pull Request. Don't forget to adjust the image name as well as annotations in `deploy/openshift-pipelines/validate_pull_request/triggertemplate_pr.yaml`. Specifically `tekton.dev/status-target-url`.

At the time of this writing, the following steps work:

```
$ sed -i 's|REPLACE_IMAGE|quay.io/koep/commit-status-tracker:v0.0.1|g' deploy/experimental/commit-status-tracker/deploy/operator.yaml
```
```
$ oc -n dusbot-dev apply -f deploy/experimental/commit-status-tracker/deploy/
```
```
$ oc -n dusbot-dev get all -l name=commit-status-tracker
NAME                                        READY   STATUS    RESTARTS   AGE
pod/commit-status-tracker-cfb8d6ff8-lxjv6   1/1     Running   0          54s

NAME                                    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE
service/commit-status-tracker-metrics   ClusterIP   172.30.163.55   <none>        8383/TCP,8686/TCP   33s

NAME                                              DESIRED   CURRENT   READY   AGE
replicaset.apps/commit-status-tracker-cfb8d6ff8   1         1         1       55s
```

Create a secret from a [GitHub token](https://github.com/settings/tokens/new). In my example, I used a dedicated [GitHub account](https://github.com/AbsolutelyNotARobot).

```
# the `-n` is essential!
$ echo -n <paste token> > $HOME/Downloads/token
$ oc -n dusbot-dev create secret generic commit-status-tracker-git-secret --from-file=$HOME/Downloads/token
```

The following steps are only required **if you use a private GitHub repository** to host the code.

```
$ ssh-keyscan github.com >> ~/.ssh/known_hosts
```
```
$ oc -n dusbot-dev create secret generic secret-to-pull-from-private-repo \
	--type=kubernetes.io/ssh-auth \
	--from-file=ssh-privatekey=$HOME/.ssh/github_deploy_key \
	--from-file=known_hosts=$HOME/.ssh/known_hosts
```
```
$ oc -n dusbot-dev annotate secret/secret-to-pull-from-private-repo tekton.dev/git-0=github.com
```

Create the AWS secret to push and pull the machine learning model from S3. I used [backblaze](http://backblaze.com/), but any S3 compatible object storage should work.

```
$ oc -n dusbot-dev create secret generic aws-access-tokens \
	--from-literal=AWS_SECRET_ACCESS_KEY=foo \
	--from-literal=AWS_ACCESS_KEY_ID=bar \
	--from-literal=AWS_DEFAULT_REGION=foobar \
	--from-literal=BUCKET_NAME=foofoo \
	--from-literal=AWS_ENDPOINT_URL='https://s3.barbar'
```

Next, set up the test environment.

## Setup test environment

```
$ oc new-project dusbot-test
```

The following secret enables the bot to talk to the [cryptocompare](https://www.cryptocompare.com/) API without being rate limited.

```
$ oc -n dusbot-test create secret generic cryptocompare-apikey --from-literal=CRYPTOCOMPARE_APIKEY=asdasdasdasdasdasdasdasd
```
This is the exact file content. NO credentials are needed.
```
$ cat credentials.yml
hangouts:
```
```
$ oc -n dusbot-test create secret generic rasa-credentials --from-file=credentials.yml -o yaml --dry-run | oc create -f -
```
Used to enable the bot to open the garage in the Red Hat Düsseldorf office.
```
$ oc -n dusbot-test create secret generic dusgarage-credentials --from-literal=DUSGARAGE_CREDENTIALS='user:password'
```
```
$ oc -n dusbot-test create secret generic aws-access-tokens \
	--from-literal=AWS_SECRET_ACCESS_KEY=foo \
	--from-literal=AWS_ACCESS_KEY_ID=bar \
	--from-literal=AWS_DEFAULT_REGION=foobar \
	--from-literal=BUCKET_NAME=foofoo \
	--from-literal=AWS_ENDPOINT_URL='https://s3.barbar'
```
```
$ oc -n dusbot-test apply -f deployment/openshift/
```

## Setup prod environment

Literally the same steps, but in a different namespace.

```
$ oc new-project dusbot-prod
```
```
$ oc -n dusbot-prod create secret generic cryptocompare-apikey --from-literal=CRYPTOCOMPARE_APIKEY=asdasdasdasdasdasdasdasd
secret/cryptocompare-apikey created
```
```
$ cat credentials.yml
hangouts:
```
```
$ oc -n dusbot-prod create secret generic rasa-credentials --from-file=credentials.yml -o yaml --dry-run | oc create -f -
```
```
$ oc -n dusbot-prod create secret generic dusgarage-credentials --from-literal=DUSGARAGE_CREDENTIALS='user:password'
```
```
$ oc -n dusbot-prod create secret generic aws-access-tokens \
	--from-literal=AWS_SECRET_ACCESS_KEY=foo \
	--from-literal=AWS_ACCESS_KEY_ID=bar \
	--from-literal=AWS_DEFAULT_REGION=foobar \
	--from-literal=BUCKET_NAME=foofoo \
	--from-literal=AWS_ENDPOINT_URL='https://s3.barbar'
```
```
$ oc -n dusbot-prod apply -f deployment/openshift/
```

# Configure Google Chat

Follow the [Google documentation](https://developers.google.com/hangouts/chat/how-tos/bots-develop) to get the initial set up going (you will need two bots to properly test changes).

The route endpoints will serve as "Bot URL". 
```
$ oc -n dusbot-test get route dusbot -o jsonpath='{..spec.host}'
```
```
$ oc -n dusbot-prod get route dusbot -o jsonpath='{..spec.host}'
```

You will have to append `/webhooks/hangouts/webhook` to the respective route URL (`https://dusbot-dusbot-test.apps.cluster.example.com/webhooks/hangouts/webhook`).

![Google Chat Configuration](https://i.imgur.com/AYzzhqu.png).