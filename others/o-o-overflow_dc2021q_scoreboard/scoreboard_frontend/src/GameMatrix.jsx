import React from "react";

/* The "Solves" tab:  team Y N N Y N ... for each challenge */

class GameMatrix extends React.Component {
  body() {
    return this.props.teamScoreboardOrder.map((team) => {
      return (
        <tr key={team.name}>
          <td className="teamname-td" key={team.name}>
            {team.name}
          </td>
          {this.solvedRow(new Set(team.solves), team.name)}
        </tr>
      );
    });
  }

  header() {
    const theHeaders = this.challenges.map((id) => {
      const n_solves = this.props.solvesByChallenge[id] || 0;
      const points = this.props.pointsByChallenge[id];
      const emoji = this.props.tagsByChallenge[id][1].get('emoji');
      const tooltip = `${id} ${emoji}\n(solved by ${n_solves})\ncurrently ${points} points`;
      const solves_str = "\u00A0(" + n_solves + ")";
      return (
        <th key={id} scope="row" title={tooltip} className="scoreboard-th">
          <span className="solves-header-emoji">{emoji}</span>{solves_str}<br/>
          <span className="solves-header-points">{points}</span>
        </th>
      );
    });

    return theHeaders;
  }

  solvedRow(solves, teamName) {
    return this.challenges.map((id) => {
      const solved = solves.has(id);
      const tooltip = "" + teamName + ": " + id + " is " + (solved ? "solved" : "unsolved");
      const cls = (solved ? "solves-td-yes" : "solves-td-no");
      return <td title={tooltip} key={id} className={cls}>{solved ? "Y" : "N"}</td>; /* TODO: emoji */
    });
  }

  render() {
    this.challenges = [];
    Object.keys(this.props.challenges).map((cat) => {
      return this.props.challenges[cat].map((chall) => {
        return this.challenges.push(chall.id);
      });
    });

    this.challenges.sort();

    return (
      <div className="table-solves">
        <table className="table table-hover table-sm">
          <thead>
            <tr>
              <th className="sticky-left scoreboard-th" scope="column">
                Team
              </th>
              {this.header()}
            </tr>
          </thead>
          <tbody>{this.body()}</tbody>
        </table>
      </div>
    );
  }
}

export default GameMatrix;
