import React from "react";
import ReactModal from "react-modal";
import { Route } from "react-router-dom";
import ChallengeMenu from "./ChallengeMenu";
import ChallengeModal from "./ChallengeModal";
import GameMatrix from "./GameMatrix";
import Navbar from "./Navbar";
import Rules from "./Rules";
import Scoreboard from "./Scoreboard";

import { split_normal_and_special_tags, EMPTY_SPLIT_TAGS } from "./utils.js";

ReactModal.setAppElement("#root");

function challengePoints(solvers, category) {
  if (!Number.isInteger(solvers) || solvers < 2) return 500;
  return parseInt(100 + 400 / (1 + 0.08 * solvers * Math.log(solvers)), 10);
}

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      challenges: {},
      lastSolveTimeByTeam: {},
      openedByCategory: {},
      solvesByChallenge: {},
      pointsByChallenge: {},
      pointsByTeam: {},
      showChallengeId: "",
      showModal: null,
      solvesByTeam: {},
      tagsByChallenge: {},
      teams: {},
      teamScoreboardOrder: [],
      unopened: {},
    };
  }

  componentDidMount() {
    this.loadChallenges();
    this.loadTeams();
  }

  handleCloseModal = () => {
    this.setState({ showModal: null });
  };

  handleOpenChallengeModal = (event) => {
    if (this.state.accessToken === "") {
      this.setState({
        showChallengeId: event.id,
        showModal: "logIn",
      });
    } else {
      this.setState({
        showChallengeId: event.id,
        showModal: "challenge",
      });
    }
  };

  loadChallenges = () => {
    fetch("/challenges.json", { method: "GET" })
      .then((response) =>
        response.json().then((body) => ({ body, status: response.status }))
      )
      .then(({ body, status }) => {
        if (status !== 200) {
          console.log(status);
          console.log(body.message);
          return;
        }
        this.processChallenges(body.message);
      })
      .catch((error) => {
        console.log(error);
      });
  };

  loadTeams = () => {
    fetch("teams.json", { method: "GET" })
      .then((response) =>
        response.json().then((body) => ({ body, status: response.status }))
      )
      .then(({ body, status }) => {
        if (status !== 200) {
          console.log(status);
          console.log(body.message);
          return;
        }
        this.setState({ teams: body.message.teams });
      })
      .catch((error) => {
        console.log(error);
      });
  };

  processChallenges = (data) => {
    const lastSolveTimeByTeam = {};
    const solvesByChallenge = {};
    const solvesByTeam = {};
    const solvesByTeamChallengeTime = {};
    data.solves.forEach(([id, team, time]) => {
      if (id in solvesByChallenge) {
        solvesByChallenge[id] += 1;
      } else {
        solvesByChallenge[id] = 1;
      }

      if (team in solvesByTeam) {
        lastSolveTimeByTeam[team] = Math.max(lastSolveTimeByTeam[team], time);
        solvesByTeam[team].push(id);
        if (!(team in solvesByTeamChallengeTime)) {
          solvesByTeamChallengeTime[team] = {};
        }
        solvesByTeamChallengeTime[team][id] = time;
      } else {
        lastSolveTimeByTeam[team] = time;
        solvesByTeam[team] = [id];
        if (!(team in solvesByTeamChallengeTime)) {
          solvesByTeamChallengeTime[team] = {};
        }
        solvesByTeamChallengeTime[team][id] = time;
      }
    });

    const challenges = {};
    const pointsByChallenge = {};
    const tagsByChallenge = {};
    let ordinal_index_for_fallbacks = 0;  // ugly, but we need something unique for fallback
    data.open.forEach(([id, tags, category, _openTime]) => {
      const split_tags = split_normal_and_special_tags(tags, ordinal_index_for_fallbacks);
      //console.log("loading chal",id, "->",split_tags);
      ordinal_index_for_fallbacks++;

      tagsByChallenge[id] = split_tags;
      pointsByChallenge[id] = challengePoints(solvesByChallenge[id], category);

      const object = {
        id,
        points: pointsByChallenge[id],
        solved: (solvesByTeam[this.state.team] || []).includes(id),
        tags: split_tags,
      };
      console.assert(category === "haiku", category);
      if (category in challenges) {
        challenges[category].push(object);
      } else {
        challenges[category] = [object];
      }
    });

    const pointsByTeam = {};
    Object.keys(solvesByTeam).forEach((team) => {
      let points = 0;
      solvesByTeam[team].forEach((id) => {
        points += pointsByChallenge[id];
      });
      pointsByTeam[team] = points;
    });

    const teamScoreboardOrder = Object.keys(pointsByTeam).map((name) => ({
      lastSolveTime: lastSolveTimeByTeam[name],
      name,
      points: pointsByTeam[name],
      solves: solvesByTeam[name],
    }));
    teamScoreboardOrder.sort((a, b) => {
      if (a.points === b.points) {
        return a.lastSolveTime - b.lastSolveTime;
      }
      return b.points - a.points;
    });

    this.setState({
      challenges,
      lastSolveTimeByTeam,
      pointsByChallenge,
      pointsByTeam,
      solvesByTeam,
      solvesByChallenge,
      tagsByChallenge,
      teamScoreboardOrder,
      unopened: data.unopened_by_category,
    });
  };

  render() {
    const solved = (this.state.solvesByTeam[this.state.team] || []).includes(this.state.showChallengeId);
    const tags = this.state.tagsByChallenge[this.state.showChallengeId] || EMPTY_SPLIT_TAGS;
    const points = this.state.pointsByChallenge[this.state.showChallengeId] || 0;
    return (
      <>
        <Navbar />
        <main role="main" className="container-fluid">
          <Route
            exact
            path="/"
            render={() => (
              <ChallengeMenu
                challenges={this.state.challenges}
                onClick={this.handleOpenChallengeModal}
                onUnload={this.handleCloseModal}
                unopened={this.state.unopened}
              />
            )}
          />
          <Route exact path="/rules" component={Rules} />
          <Route
            exact
            path="/scoreboard"
            render={() => (
              <Scoreboard
                tagsByChallenge={this.state.tagsByChallenge}
                lastSolveTimeByTeam={this.state.lastSolveTimeByTeam}
                pointsByTeam={this.state.pointsByTeam}
                solvesByTeam={this.state.solvesByTeam}
                teamScoreboardOrder={this.state.teamScoreboardOrder}
                team={this.state.team}
                teams={this.state.teams}
              />
            )}
          />
          <Route
            exact
            path="/solves"
            render={() => (
              <GameMatrix
                challenges={this.state.challenges}
                solvesByChallenge={this.state.solvesByChallenge}
                teamScoreboardOrder={this.state.teamScoreboardOrder}
                tagsByChallenge={this.state.tagsByChallenge}
                pointsByChallenge={this.state.pointsByChallenge}
              />
            )}
          />

          <ReactModal
            className="challenge-modal"
            contentLabel="Challenge Modal"
            isOpen={this.state.showModal === "challenge"}
            onRequestClose={this.handleCloseModal}
          >
            <ChallengeModal
              challengeId={this.state.showChallengeId}
              onClose={this.handleCloseModal}
              onSolve={this.loadChallenges}
              solved={solved}
              numSolved={
                this.state.solvesByChallenge[this.state.showChallengeId] || 0
              }
              tags={tags}
              points={points}
            />
          </ReactModal>
        </main>
      </>
    );
  }
}
export default App;
