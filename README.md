# chess2

The chess2 website API made in python with FastAPI.

Chess2 is chess website with many new pieces and rules.

2 players can match against each other if they are rated similarly and choose the same game settings.
You are also able to play as a guest, but your rating and game history will not be saved.

A video from before the rewrite:

https://github.com/YishaiYosifov/chess2-backend/assets/74960133/01f7e833-a1e8-40bc-8bed-caacc3544d52

## Installation

This project uses docker with the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) vscode extension.
To get started, simply open the project in vscode and reopen it in a dev container.

For manual setup, you can use docker compose by running the following command:

```bash
$ docker compose up
```

## Config

The config file is located in `app/schemas/config_schema.py`.

Do not directly edit that file to configure the application - the schema is automatically updated with the values in the `.env` file.
You can configure which file it reads by setting the `ENV` environment variable.

## Features

### User Authentication

User authentication is handled with JWT tokens. When a user logs in, they receive a refresh and an access token. The access token expires within 30 minutes while the refresh token expires within 30 days. The refresh token is used to regenerate the access token after it expires.

### Guest Users

Users can also enter the matchmaking pool without creating an account. Guest users can only play against guest users, and authed users can only play against authed users. Guest users can be created with the `GET /auth/guest-account` endpoint.

Guest users are implemented using a polymorphic relationship in the User sqlalchemy model. A cron job automatically deletes guest accounts that have not refreshed their access token in longer than 30 minutes.

### Matchmaking

A matchmaking system allows players to play against similar rated players. To join the pool, you need to send a request to `POST /game-requests/pool/join`. If a game request with a similar elo rating and the same game settings exists, a game will be created and the game token will be returned. Otherwise, a game request will be created.

### Profile & Settings

You can view a users past games, ratings and profile in the `/profile/{target}` router. Target can be `me`, a username or a user id.

User settings can be updated in the `/settings` router. Settings include

### Gameplay

Pieces are implemented by inheriting the `Piece` class and providing offsets. Offsets are how much the piece has to move each step in order to find all its legal moves.

## Key modules and directories

-   `app/routers` contains all the routers (endpoints)
    -   `app/routers/game_requests.py` endpoints for the matchmaking pool
    -   `app/routers/auth/py` endpoints for logging in, signing up, refreshing access tokens and creating guest accounts
-   `app/models` all the sqlalchemy modules
-   `app/game` piece and board logic
    -   `app/game/pieces.py` piece implementation
    -   `app/game/board.py` class for handling the state of the board
-   `app/services`
    -   `app/services/game_request_service.py` service for searching / entering the pool and starting a request
    -   `app/services/jwt_service.py` all encoding / decoding jwt logic
    -   `app/services/ws_service`
        -   `app/services/ws_service/ws_server.py` logic for horizontally scaling websocket handling using redis pubsub
-   `app/crud`
    -   `app/crud/game_request_crud.py` logic for searching and creating a request
    -   `app/crud/user_crud.py` logic for fetching, creating and deleting authed and guest users

## Testing

To run the tests, run the following command:

```bash
$ pytest
```

To run the pytest test watcher, run the following command:

```bash
$ ptw .
```

Tests are located in the `tests` folder, mirroring the structure of the `app` directory.
To maintain readability, test modules may be broken up into smaller, more focused ones if they are getting too big.
