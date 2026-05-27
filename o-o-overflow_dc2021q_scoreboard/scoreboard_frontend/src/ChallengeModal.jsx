import PropTypes from "prop-types";
import exact from "prop-types-exact";
import React from "react";
import showdown from "showdown";

/* XXX: TO REMOVE TAGS: remove the tagthingy */

class ChallengeModal extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      alertCSS: "",
      description: "",
      flag: "",
      status: "",
    };
    this.worker = new Worker("worker.js");
    this.worker.onmessage = (message) => {
      if (message.data.complete) {
        const status =
          message.data.digest === this.state.flagHash
            ? "success!"
            : "incorrect flag";
        this.setState({ status });
      }
    };
  }

  componentDidMount() {
    this.loadData();
  }

  componentWillUnmount() {
    this.worker.terminate();
  }

  handleFlagChange = (event) => {
    this.setState({ alertCSS: "", flag: event.target.value });
  };

  handleKeyPress = (event) => {
    if (event.key === "Enter") {
      this.handleSubmit();
    }
  };

  handleSubmit = () => {
    if (this.state.flag.length < 1 || this.state.flag.length > 160) {
      this.setState({ status: "invalid flag" });
    } else {
      this.worker.postMessage(this.state.flag);
    }
  };

  loadData = () => {
    this.setState({ description: "Loading..." });
      fetch("scoreboard.json", { method: "GET" })
      .then((response) =>
        response.json().then((body) => ({ body, status: response.status }))
      )
      .then(({ body, status }) => {
        if (status !== 200) {
          console.log(status);
          console.log(body.message);
          return;
        }
        const converter = new showdown.Converter({
          literalMidWordUnderscores: true,
          simplifiedAutoLink: true,
        });
        const description = converter.makeHtml(
          body[this.props.challengeId]["description"]
        ); /* html from chalmanager */
        const flagHash = body[this.props.challengeId]["flag_hash"];
        this.setState({ description, flagHash });
      });
  };

  render() {
    let status; /* magic name or something? */
    if (this.state.status !== "") {
      let css;
      if (this.state.alertCSS) {
        css = `alert ${this.state.alertCSS}`;
      } else {
        css = "alert alert-secondary";
      }
      status = (
        <div className={css}>Status: {this.state.status}</div>
      );
    }

    const [normal_tags, special_attrs] = this.props.tags;
    const tag_spans = normal_tags.map((tag, index) => {
        return (<span className="tag-boxy-thing" key={index}>{`${tag.trim()}`}</span>);
      });
    const tagthingy = (<div className="tagthingy">{tag_spans}</div>);

    const my_emoji = special_attrs.get('emoji')
    const my_points = this.props.points;
    const emojispan = (<span className="emojifont">{`${my_emoji}`}</span>);
    const grantsline = (
        <div className="grantsline">
          {`This station grants`}
          {emojispan}
          {`and is currently ${my_points} points`}
        </div>);

    let form_submission = "";

    if (!this.props.solved) {
      form_submission = (
        <>
          <label htmlFor="flag" className="sr-only">
            Flag
          </label>
          <input
            id="flag"
            className="form-control"
            placeholder="flag (format: OOO{…})"
            onChange={this.handleFlagChange}
            onKeyPress={this.handleKeyPress}
            type="text"
            value={this.state.flag}
          />
          <input
            className="btn btn-primary"
            onClick={this.handleSubmit}
            type="button"
            value="Submit Flag"
          />
        </>
      );
    } else {
      form_submission = (
        <span className="already-solved-msg">This radio station already likes you :)</span>
      );
    }

    const solve_string =
      this.props.numSolved === 1 ? "1 solve" : `${this.props.numSolved} solves`;

    const chalmodalStyle = {
        'maxWidth': '60em',
        'minWidth': '600px',
        width: 'fit-content',
    };

    return (
      <div className="modal-dialog" role="document" style={chalmodalStyle}>
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">{`${this.props.challengeId} (${solve_string})`}</h5>
            <button
              aria-label="Close"
              className="close"
              onClick={this.props.onClose}
              type="button"
            >
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div className="modal-body">
            <div dangerouslySetInnerHTML={{ __html: this.state.description }} />
            {tagthingy}
            {grantsline}
            {status}
          </div>
          <div className="modal-footer">
            {form_submission}
            <button
              className="btn btn-secondary"
              onClick={this.props.onClose}
              type="button"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }
}
ChallengeModal.propTypes = exact({
  challengeId: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
  onSolve: PropTypes.func.isRequired,
  solved: PropTypes.bool.isRequired,
  numSolved: PropTypes.number.isRequired,
  tags: PropTypes.array.isRequired,
  points: PropTypes.number.isRequired,
});
export default ChallengeModal;
