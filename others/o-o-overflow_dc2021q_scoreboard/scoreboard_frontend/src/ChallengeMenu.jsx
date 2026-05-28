import PropTypes from "prop-types";
import exact from "prop-types-exact";
import React from "react";
import ChallengeSection from "./ChallengeSection";

/* There's actually only one ChallengeSection now (haiku) */



class ChallengeMenu extends React.Component {
  constructor(props) {
    super(props);

    this.sectionOrder = ["haiku"];
  }

  componentWillUnmount = () => {
    this.props.onUnload();
  };

  buildSections = (sectionTitle) => {
    const openChallenges = this.props.challenges[sectionTitle] || [];
    const unopenedChallenges = Array.from(
      Array(this.props.unopened[sectionTitle] || 0),
      (_, i) => ({ unopened: i + 1000 })
    );
    return (
      <ChallengeSection
        challenges={openChallenges.concat(unopenedChallenges)}
        key={sectionTitle}
        onClick={this.props.onClick}
        title={sectionTitle}
      />
    );
  };

  render() {
    const sections = this.sectionOrder.map(this.buildSections);
    return (
      <>
        <div id="thebigdiv">
            {sections}
        </div>
        <footer className="chalmenu-footer">
          You can't stop the signal
        </footer>
      </>
    );
  }
}
ChallengeMenu.propTypes = exact({
  challenges: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.object))
    .isRequired,
  onClick: PropTypes.func.isRequired,
  onUnload: PropTypes.func.isRequired,
  unopened: PropTypes.objectOf(PropTypes.number).isRequired,
});
export default ChallengeMenu;
