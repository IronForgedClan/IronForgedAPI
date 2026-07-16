<h1 align="center">Iron Forged API</h1>
<p align="center">
<img alt="API Version" src="https://img.shields.io/github/v/release/IronForgedClan/IronForgedApi?include_prereleases&label=api">
<a href="https://github.com/IronForgedClan/IronForgedApi/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/IronForgedClan/IronForgedApi"></a>
<a href="https://github.com/psf/black"><img alt="Code style: Black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

<p align="center">A REST API exposing member, ingot, and score data to authenticated consumers for the Iron Forged Old School RuneScape clan.</p>

For the full endpoint reference, see [API.md](./API.md).

## Setup

This setup guide assumes use of a Linux terminal.

### Set up SSH authentication with GitHub

This project uses a private submodule that requires SSH authentication.

> [!IMPORTANT]
> You must set up SSH keys with GitHub before cloning. HTTPS will not work for
> the private submodule.

#### Generate SSH key (if you don't have one)

```sh
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter to accept default location
# Optionally enter a passphrase
```

#### Add SSH key to ssh-agent

```sh
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

#### Add SSH key to GitHub

1. Copy your public key:
   ```sh
   cat ~/.ssh/id_ed25519.pub
   ```
2. Go to GitHub -> Settings -> SSH and GPG keys -> New SSH key
3. Paste your public key and save

#### Test your connection

```sh
ssh -T git@github.com
# Should respond: "Hi username! You've successfully authenticated..."
```

For more details, see
[GitHub's SSH documentation](https://docs.github.com/en/authentication/connecting-to-github-with-ssh).

### Clone the repository

Navigate to a location you want to store the project. Then run the following
command to clone this repository to your machine.

```sh
git clone git@github.com:IronForgedClan/IronForgedApi.git
```

### Initialize Data Submodule

This project uses a private git submodule for data files.

> [!IMPORTANT]
> You'll need access to the `IronForgedBot_Data` private repository. Contact
> repository maintainers if you don't have access.

#### First-time setup (after cloning)

```sh
git submodule init
git submodule update
```

#### Or clone with submodules in one step

```sh
git clone --recurse-submodules git@github.com:IronForgedClan/IronForgedApi.git
```

#### Updating data files

```sh
git submodule update --remote data
```

> [!NOTE]
> If you see errors about missing `data/*.json` files, ensure the submodule is
> initialized using the commands above.

### Docker

This project uses [Docker](https://www.docker.com/) and
[Docker Compose](https://docs.docker.com/compose/) to streamline setup and
deployment.

### Requirements

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- A database the api can read and write (the included `db` service works
  for dev)

### Secrets

Secrets are written as key value pairs in the `.env` file.

To create a `.env` file from the example file run:

```sh
cp .env.example .env
```

Now you can modify the example `.env` file with your values.

> [!WARNING]
> Never check your `.env` file into source control!

#### Keys

The api reads env vars from two sources: the shared
[IronForgedCore](https://github.com/IronForgedClan/IronForgedCore) `BaseConfig`
(database URL, log levels, WOM keys, etc.) and the api-specific
`ApiConfig` (`API_*` keys below).

| Key                  | Explanation                                                                       | Source                                              |
| -------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------- |
| ENVIRONMENT          | Defines the environment the api is running in: 'dev', 'staging', 'prod'           |                                                     |
| TEMP_DIR             | The location on disk where temporary files are stored. Default value is `./temp`. |                                                     |
| GUILD_ID             | The ID of the Discord guild. Required by `BaseConfig`.                            | The bot's Discord server: right click, "Copy Server ID". |
| BOT_TOKEN            | The unique token for the application. Required by `BaseConfig`.                   | The bot's Discord Developer Portal.                 |
| WOM_API_KEY          | The unique key for connecting to the Wise Old Man API.                            | Ask a project admin.                                |
| WOM_GROUP_ID         | The unique ID for the clan group on Wise Old Man.                                 | Ask a project admin.                                |
| WOM_LTM_BASE_URL     | Base URL for the Limited Time Mode WOM tracker. Optional.                         | Ask a project admin.                                |
| WOM_LTM_GROUP_ID     | The unique ID for the LTM clan group on Wise Old Man. Optional.                   | Ask a project admin.                                |
| AUTOMATION_CHANNEL_ID | The unique ID of the channel that automation messages will be sent to.            | Discord server channel: right click, "Copy Channel ID". |
| RAFFLE_CHANNEL_ID    | The unique ID of the channel that will house the raffle.                          | Discord server channel: right click, "Copy Channel ID". |
| INGOT_SHOP_CHANNEL_ID | The unique ID of the ingot shop channel.                                          | Discord server channel: right click, "Copy Channel ID". |
| RULES_CHANNEL_ID     | The unique ID of the rules channel.                                               | Discord server channel: right click, "Copy Channel ID". |
| RANKINGS_CHANNEL_ID  | The unique ID of the rankings channel.                                            | Discord server channel: right click, "Copy Channel ID". |
| BOT_COMMANDS_CHANNEL_ID | The unique ID of the bot commands channel.                                        | Discord server channel: right click, "Copy Channel ID". |
| BOT_CHANGELOG_CHANNEL_ID | The unique ID of the bot changelog channel.                                       | Discord server channel: right click, "Copy Channel ID". |
| CREATE_TICKET_CHANNEL_ID | The unique ID of the channel where users submit feedback or support tickets.      | Discord server channel: right click, "Copy Channel ID". |
| DB_ROOT              | The password used by the root database account.                                   | Generate a secure password.                         |
| DB_USER              | The name of the user account the api will use to access the database.             | Any value. Eg: test_user                            |
| DB_PASS              | The password of the account the api will use to access the database.              | Generate a secure password.                         |
| DB_NAME              | The name of the database the api will attempt to connect to.                      | Any value. Eg: api_test                             |
| LOG_LEVEL            | File handler log level. Default: `INFO`.                                          | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`     |
| LOG_CONSOLE_LEVEL    | Console log level (overrides environment-based default).                          | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`     |
| LOG_DIR              | Directory for log files. Default: `./logs`.                                       | Any valid directory path.                           |
| LOG_FILE_MAX_BYTES   | Max size of each log file before rotation. Default: `10000000` (10MB).             | Integer (bytes).                                    |
| LOG_FILE_BACKUP_COUNT | Number of backup log files to keep. Default: `10`.                                | Integer.                                            |
| LOG_JSON_FORMAT      | Use JSON formatting for logs. Default: `false`.                                   | `true`, `false`                                     |
| API_HOST             | Bind address for the API. Default: `0.0.0.0`.                                     | Any valid host.                                     |
| API_PORT             | Port the API listens on. Default: `8080`.                                         | Integer 1-65535.                                    |
| API_RATE_LIMIT       | Per-consumer request limit. Default: `30`.                                        | Integer. `0` disables.                              |
| API_TRUSTED_HOSTS    | Comma-separated trusted reverse-proxy IPs for X-Forwarded-For parsing.            | Comma-separated IPs.                                |
| API_CORS_ORIGINS     | Comma-separated allowed CORS origins. Default empty (no CORS).                    | Comma-separated URLs.                               |

### Migrations

You will need to run the database migrations before the api will be able to use
the database. To do so, you can run the following command. You will need to do
this every time the database schema changes. Migration files live inside the
`ironforgedcore/alembic/versions` directory inside the
[IronForgedCore](https://github.com/IronForgedClan/IronForgedCore) package, which
is installed via `pyproject.toml` from a git URL.

```sh
make migrate
```

> [!NOTE]
> There is a chicken and egg issue here where you can't run the project without
> a database and its migrations, but you can't run the migrations without a
> database to talk to. In order to resolve this the first time the project is
> set up, you will need to spin up the initial containers with `make up` before
> continuing to run the migrations. Be warned that you will see errors in the
> output, as we haven't run the migrations yet.

### Running inside Docker

Now everything is ready, you can bring the project online with the following
command.

```sh
make up
```

You should now see in the console the database spinning up, followed by the api.
The api should then start listening on `http://localhost:8080`. The `make up`
target uses the dev image with `uvicorn --reload`, so code changes are picked
up live.

#### Stopping the project

So you've done some work, and want to pack it in for the day? You can kill the
project by either doing `CTRL+C` twice in the terminal window running the docker
containers. Or with the following command if running detached.

```sh
make down
```

## Makefile

This project includes a `Makefile` with handy commands to simplify development.
If at any point a `make` command doesn't work, you can open the `Makefile` to
view its source command and try running that instead.

### Commands

- `make up`\
  Starts the database and api (dev) together. The dev service mounts the
  source tree and uses `uvicorn --reload`, so code changes are picked up
  live.

- `make up-prod`\
  Starts the database and api from the built prod image. Use this to verify
  a production build without the dev mount.

- `make down`\
  Stops and removes the containers.

- `make test`\
  Runs the test suite.

- `make format`\
  Formats the codebase using Black formatter.

- `make shell`\
  Opens an interactive bash shell inside the api container.

- `make migrate`\
  Runs the database migrations.

- `make revision`\
  Creates a new database migration. Expects a `DESC` parameter. Eg:
  `make revision DESC="added a new column to the members table"`

- `make downgrade`\
  Reverts the most recent database migration.

- `make build-prod`\
  Builds the api prod image.

- `make rmi-prod`\
  Removes the api prod image.

- `make api-consumer-interactive`\
  Walk through creating, perm-granting or revoking, enabling or disabling,
  rotating, and deleting API consumers, with a guided prompt flow.
  Available perms are read from `api/permissions.py:KNOWN_PERMS` so the menu
  stays in sync with the code.

- `make api-consumer-list`\
  Print a table of all registered API consumers and their current perms
  (for scripting).

- `make clean`\
  Stops containers, removes project containers and images, and prunes unused
  Docker resources to free up disk space.

## Tooling

As all dependencies are installed within the Docker container, you might find
your editor complaining it can't find the library referenced in the code. To
alleviate this we can install the project dependencies in the project root so
our tooling can pick them up.

### Virtual Environment

It is recommended to use Python's virtual environments when installing
dependencies.

```sh
python -m venv .venv
```

This will create a directory `.venv`. To activate the environment, run:

```sh
source .venv/bin/activate
```

### Requirements

The project requirements are listed in `requirements.txt` file. To install, run:

```sh
pip install -r requirements.txt
```

## Testing

All test files live within the `tests` directory. The structure within this
directory mirrors the source tree (`api`).

To execute the entire test suite run:

```sh
make test
```

When creating new test files, the filename must follow the pattern `*_test.py`.
And the class name must follow the pattern `Test*`.

## API Reference

See [API.md](./API.md) for the full endpoint reference, including required
perms, response shapes, and the audit envelope. The Bruno collection under
`api/bruno/` is the source of truth for live request examples and stays in
sync with the routers.

## Contributing

Contributions must:

- Address a specific issue by ticket number.
- Pass all tests in the test suite.
- Code style must conform to the black formatter.
- If the contribution adds new functionality, tests covering this must also be
  added.

### Formatting

This codebase uses the [Black](https://github.com/psf/black) formatter.
Extensions available for many
[popular editors](https://black.readthedocs.io/en/stable/integrations/editors.html).
This is enforced through a workflow that runs on all pull requests into main.

> By using Black, you agree to cede control over minutiae of hand-formatting. In
> return, Black gives you speed, determinism, and freedom from pycodestyle
> nagging about formatting. You will save time and mental energy for more
> important matters.
