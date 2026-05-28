import PropTypes from "prop-types";
import React from "react";

function chalIcon(challengeId, tagsByChallenge) {
  const x = tagsByChallenge[challengeId];
  console.assert(x.length === 2, tagsByChallenge, challengeId, x);
  const special_attrs = x[1];
  const my_emoji = special_attrs.get('emoji');
  return (
    <span
      className={`scoreboard-chal-span`}
      key={challengeId}
      title={challengeId}
    >{my_emoji}</span>
  );
}

function Scoreboard(props) {
  var num = 1;
  const teams = props.teamScoreboardOrder.map((team) => ({
    lastSolveTime: team.lastSolveTime,
    name: team.name,
    num: num++,
    points: props.pointsByTeam[team.name],
    solves: team.solves.map((id) =>
      chalIcon(id, props.tagsByChallenge)
    ),
  }));

  function ctfTimeLink(teamName) {
    const ctfTimeTeamID = props.teams[teamName];
    if (ctfTimeTeamID !== undefined) {
      return (
        <a
          href={`https://ctftime.org/team/${ctfTimeTeamID}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          {teamName}
        </a>
      );
    }
    return teamName;
  }

  const teamRows = teams.map((team) => (
    <tr key={team.name} id={team.name}>
      <td>{team.num}</td>
      <td>{team.points}</td>
      <td className="teamname-td">{ctfTimeLink(team.name)}</td>
      <td>{team.solves}</td>
    </tr>
  ));

  function handleClick() {
    const element = document.getElementById(props.team);
    if (element) {
      window.scroll({
        behavior: "smooth",
        top: element.offsetTop,
      });
    }
  }

  const teamLink = props.team ? (
    <button type="button" className="btn btn-link" onClick={handleClick}>
      (My Team)
    </button>
  ) : null;

  return (
    <div className="table-scoreboard">
      <table className="table table-hover table-sm">
        <thead>
          <tr>
            <th className="scoreboard-th" scope="col">Place</th>
            <th className="scoreboard-th" scope="col">Points</th>
            <th className="scoreboard-th" scope="col">Team {teamLink}</th>
            <th className="scoreboard-th" scope="col">Completed</th>
          </tr>
        </thead>
        <tbody>{teamRows}</tbody>
      </table>
    </div>
  );
}
Scoreboard.propTypes = {
  tagsByChallenge: PropTypes.objectOf(PropTypes.array).isRequired,
  lastSolveTimeByTeam: PropTypes.objectOf(PropTypes.number).isRequired,
  pointsByTeam: PropTypes.objectOf(PropTypes.number).isRequired,
  solvesByTeam: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.string))
    .isRequired,
  teams: PropTypes.objectOf(PropTypes.number).isRequired,
};
export default Scoreboard;
