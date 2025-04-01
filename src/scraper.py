import numpy as np
import pandas as pd
from nhlpy import NHLClient


def second_diff(time1, time2):
    minutes1 = int(time1[0:2])
    minutes2 = int(time2[0:2])
    seconds1 = int(time1[3:5])
    seconds2 = int(time2[3:5])
    return abs((minutes2 * 60 + seconds2) - (minutes1 * 60 + seconds1))


def get_game_ids(seasons: list = [20242025]) -> list:
    client = NHLClient()

    game_ids = []

    teams = client.teams.teams_info()
    team_abbrs = []

    for item in teams:
        abbr = item["abbr"]
        team_abbrs.append(abbr)

    for abbreviation in team_abbrs:
        for season in seasons:

            if abbreviation == "UTA" and season != 20242025:
                abbreviation = "ARI"

            games = client.schedule.get_season_schedule(
                team_abbr=abbreviation, season=season
            )["games"]

            for game in games:
                if game["gameType"] == 1:
                    continue

                id = game["id"]
                if id not in [game_ids]:
                    game_ids.append(id)
    return game_ids


def shot_scraper2(game_ids: list) -> pd.DataFrame:
    client = NHLClient()
    rows = []
    for game_id in game_ids:
        game_data = client.game_center.play_by_play(game_id=game_id)
        home_id = game_data["homeTeam"]["id"]
        away_id = game_data["awayTeam"]["id"]
        pbp = game_data["plays"]

        player_dict = {
            player["playerId"]: player["firstName"]["default"]
            + " "
            + player["lastName"]["default"]
            for player in game_data["rosterSpots"]
        }

        for idx, play in enumerate(pbp):

            if play["typeDescKey"] not in ["missed-shot", "goal", "shot-on-goal"]:
                continue

            home = 0
            away = 0
            rebound = 0
            rush = 0

            try:
                if home_id == play["details"]["eventOwnerTeamId"]:
                    home = 1
                else:
                    away = 1

                if (home == 1 and play["situationCode"][0] == "0") or (
                    away == 1 and play["situationCode"][3] == "0"
                ):
                    continue

                if home == 1:
                    team_id = home_id
                else:
                    team_id = away_id

                if idx > 0:
                    time_diff = second_diff(
                        play["timeInPeriod"], pbp[idx - 1]["timeInPeriod"]
                    )

                    if pbp[idx - 1]["typeDescKey"] == "blocked-shot" and time_diff <= 2:
                        rebound = 1

                    if (
                        pbp[idx - 1]["typeDescKey"] in ["missed-shot", "shot-on-goal"]
                    ) and time_diff <= 3:
                        rebound = 1

                    if (
                        (pbp[idx - 1]["typeDescKey"] in ["takeaway", "giveaway"])
                        and time_diff <= 4
                        and pbp[idx - 1]["details"]["zoneCode"] in ["N", "D"]
                    ):
                        rush = 1

                home_skaters = play["situationCode"][2]
                away_skaters = play["situationCode"][1]
                shot_class = play["typeDescKey"]
                x_coord = abs(play["details"]["xCoord"])
                y_coord = play["details"]["yCoord"]
                shot_type = play["details"]["shotType"]
                shooter = None
                shooter_id = None
                goalie_id = play["details"]["goalieInNetId"]
                goalie = player_dict[goalie_id]
                last_play = pbp[idx - 1]["typeDescKey"]
                zone = play["details"]["zoneCode"]

                if shot_class == "goal":

                    shooter_id = play["details"]["scoringPlayerId"]
                    shooter = player_dict[shooter_id]

                else:

                    shooter_id = play["details"]["shootingPlayerId"]
                    shooter = player_dict[shooter_id]

                rows.append(
                    [
                        game_id,
                        team_id,
                        home,
                        last_play,
                        rebound,
                        rush,
                        home_skaters,
                        away_skaters,
                        x_coord,
                        y_coord,
                        shooter_id,
                        shooter,
                        goalie_id,
                        goalie,
                        shot_type,
                        zone,
                        shot_class,
                    ]
                )
            except:
                continue

    header = [
        "game_id",
        "team_id",
        "home",
        "last_play",
        "rebound",
        "rush",
        "home_skaters",
        "away_skaters",
        "x_coord",
        "y_coord",
        "shooter_id",
        "shooter",
        "goalie_id",
        "goalie",
        "shot_type",
        "zone",
        "shot_class",
    ]
    df = pd.DataFrame(rows, columns=header)
    return df


def shot_scraper(game_ids: list) -> pd.DataFrame:
    client = NHLClient()
    rows = []
    for game_id in game_ids:
        game_data = client.game_center.play_by_play(game_id=game_id)
        home_id = game_data["homeTeam"]["id"]
        away_id = game_data["awayTeam"]["id"]
        pbp = game_data["plays"]

        player_dict = {
            player["playerId"]: player["firstName"]["default"]
            + " "
            + player["lastName"]["default"]
            for player in game_data["rosterSpots"]
        }

        stats_dict = {
            player["playerId"]: (
                [
                    client.stats.player_career_stats(player["playerId"])["position"],
                    client.stats.player_career_stats(player["playerId"])[
                        "shootsCatches"
                    ],
                    client.stats.player_career_stats(player["playerId"])[
                        "featuredStats"
                    ]["regularSeason"]["career"]["savePctg"],
                ]
                if client.stats.player_career_stats(player["playerId"])["position"]
                == "G"
                else [
                    client.stats.player_career_stats(player["playerId"])["position"],
                    client.stats.player_career_stats(player["playerId"])[
                        "shootsCatches"
                    ],
                    client.stats.player_career_stats(player["playerId"])[
                        "featuredStats"
                    ]["regularSeason"]["career"]["shootingPctg"],
                ]
            )
            for player in game_data["rosterSpots"]
        }

        for idx, play in enumerate(pbp):

            if play["typeDescKey"] not in ["missed-shot", "goal", "shot-on-goal"]:
                continue

            home = 0
            away = 0
            rebound = 0
            rush = 0

            try:
                if home_id == play["details"]["eventOwnerTeamId"]:
                    home = 1
                else:
                    away = 1

                if (home == 1 and play["situationCode"][0] == "0") or (
                    away == 1 and play["situationCode"][3] == "0"
                ):
                    continue

                if home == 1:
                    team_id = home_id
                else:
                    team_id = away_id

                if idx > 0:
                    time_diff = second_diff(
                        play["timeInPeriod"], pbp[idx - 1]["timeInPeriod"]
                    )

                    if pbp[idx - 1]["typeDescKey"] == "blocked-shot" and time_diff <= 2:
                        rebound = 1

                    if (
                        pbp[idx - 1]["typeDescKey"] in ["missed-shot", "shot-on-goal"]
                    ) and time_diff <= 3:
                        rebound = 1

                    if (
                        (pbp[idx - 1]["typeDescKey"] in ["takeaway", "giveaway"])
                        and time_diff <= 4
                        and pbp[idx - 1]["details"]["zoneCode"] in ["N", "D"]
                    ):
                        rush = 1

                home_skaters = play["situationCode"][2]
                away_skaters = play["situationCode"][1]
                shot_class = play["typeDescKey"]
                x_coord = abs(play["details"]["xCoord"])
                y_coord = play["details"]["yCoord"]
                shot_type = play["details"]["shotType"]
                shooter = None
                shooter_id = None
                goalie_id = play["details"]["goalieInNetId"]
                goalie = player_dict[goalie_id]
                last_play = pbp[idx - 1]["typeDescKey"]
                zone = play["details"]["zoneCode"]

                if shot_class == "goal":

                    shooter_id = play["details"]["scoringPlayerId"]
                    shooter = player_dict[shooter_id]

                else:

                    shooter_id = play["details"]["shootingPlayerId"]
                    shooter = player_dict[shooter_id]

                position = stats_dict[shooter_id][0]
                shoots = stats_dict[shooter_id][1]
                career_shooting_pct = stats_dict[shooter_id][2]
                goalie_catches = stats_dict[goalie_id][1]
                career_save_pct = stats_dict[goalie_id][2]

                rows.append(
                    [
                        game_id,
                        team_id,
                        home,
                        last_play,
                        rebound,
                        rush,
                        home_skaters,
                        away_skaters,
                        x_coord,
                        y_coord,
                        shooter_id,
                        shooter,
                        position,
                        shoots,
                        career_shooting_pct,
                        goalie_id,
                        goalie,
                        goalie_catches,
                        career_save_pct,
                        shot_type,
                        zone,
                        shot_class,
                    ]
                )
            except:
                continue

    header = [
        "game_id",
        "team_id",
        "home",
        "last_play",
        "rebound",
        "rush",
        "home_skaters",
        "away_skaters",
        "x_coord",
        "y_coord",
        "shooter_id",
        "shooter",
        "position",
        "shoots",
        "career_shooting_pct",
        "goalie_id",
        "goalie",
        "goalie_catches",
        "career_save_pct",
        "shot_type",
        "zone",
        "shot_class",
    ]
    df = pd.DataFrame(rows, columns=header)
    return df


def get_skater_stats(df: pd.DataFrame) -> pd.DataFrame:

    client = NHLClient()
    stats_list = []
    goalie_stats = []
    stats_dict = {}
    goalie_stats_dict = {}

    shooter_ids = df["shooter_id"].tolist()
    goalie_ids = df["goalie_id"].tolist()

    for id in shooter_ids:
        if id not in stats_dict.keys():
            stats = client.stats.player_career_stats(id)
            try:
                stats_dict[id] = {
                    "position": stats["position"],
                    "hand": stats["shootsCatches"],
                    "pct": stats["featuredStats"]["regularSeason"]["career"][
                        "shootingPctg"
                    ],
                }
            except:
                stats_dict[id] = {
                    "position": stats["position"],
                    "hand": stats["shootsCatches"],
                    "pct": None,
                }

        position = stats_dict[id]["position"]
        shooter_hand = stats_dict[id]["hand"]
        shooting_pct = stats_dict[id]["pct"]
        stats_list.append((position, shooter_hand, shooting_pct))

    for id in goalie_ids:
        if id not in goalie_stats_dict.keys():
            stats = client.stats.player_career_stats(id)
            try:
                goalie_stats_dict[id] = {
                    "hand": stats["shootsCatches"],
                    "pct": stats["featuredStats"]["regularSeason"]["career"][
                        "savePctg"
                    ],
                }
            except:
                goalie_stats_dict[id] = {"hand": stats["shootsCatches"], "pct": None}

        shooter_hand = goalie_stats_dict[id]["hand"]
        save_pct = goalie_stats_dict[id]["pct"]
        goalie_stats.append((shooter_hand, save_pct))

    goalie_header = ["glove_hand", "save_pct"]
    goalie_df = pd.DataFrame(goalie_stats, columns=goalie_header)

    header = ["position", "shooter_hand", "shooting_pct"]
    stats_df = pd.DataFrame(stats_list, columns=header)

    final_df = pd.concat([df, stats_df, goalie_df], axis=1)
    return final_df


def angle(x_coord, y_coord):
    x_centered = 89 - x_coord
    return round(np.degrees(np.arctan(y_coord / x_centered)), 2)


def get_processed_data(df: pd.DataFrame) -> pd.DataFrame:
    df["angle"] = angle(df["x_coord"], df["y_coord"])
    df["shot_on_glove"] = df["shooter_hand"] + df["glove_hand"]
    df["home_skaters"] = df["home_skaters"].astype(int)
    df["away_skaters"] = df["away_skaters"].astype(int)
    df = df[df["home_skaters"] >= 3]
    df = df[df["away_skaters"] >= 3]
    df["situation"] = df.apply(
        lambda row: (
            "EV"
            if row["home_skaters"] == row["away_skaters"]
            else ("PP" if row["home_skaters"] > row["away_skaters"] else "SH")
        ),
        axis=1,
    )

    df = df.drop(
        ["game_id", "team_id", "shooter_id", "shooter", "goalie", "goalie_id"], axis=1
    )
    df["target"] = np.where(df["shot_class"] == "goal", 1, 0)

    home_mapping = {}
    home_mapping[0] = "Away"
    home_mapping[1] = "Home"

    rebound_mapping = {}
    rebound_mapping[0] = "No rebound"
    rebound_mapping[1] = "Rebound"

    rush_mapping = {}
    rush_mapping[0] = "No rush"
    rush_mapping[1] = "Rush"

    df["home"] = df["home"].replace(home_mapping)
    df["rebound"] = df["rebound"].replace(rebound_mapping)
    df["rush"] = df["rush"].replace(rush_mapping)

    df = df.drop("shot_class", axis=1)
    return df
