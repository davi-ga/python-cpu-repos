import React from "react";
import { Link, NavLink } from "react-router-dom";

function Navbar(props) {

  const leftLinks = [
    ["Challenges", "/", true],
    ["Rules", "/rules"],
    ["Scoreboard", "/scoreboard"],
    ["Solves", "/solves"],
  ].map((item) => (
    <li className="nav-item" key={item[0]}>
      <NavLink className="nav-link" exact={item[2]} to={item[1]}>
        {item[0]}
      </NavLink>
    </li>
  ));

  // TODO: could I make it show on mouse movement?
  return (
    <nav className="navbar navbar-expand navbar-dark">
      <Link className="navbar-brand" to="/">
        DC29 Quals
      </Link>
      <div className="navbar-collapse">
        <ul className="navbar-nav mr-auto">
            {leftLinks}
            <li className="nav-item" key="Chat"><a className="nav-link" href="https://discord.gg/defcon" target="_blank" rel="noopener noreferrer" title="CTF area at the bottom">Chat</a></li>
        </ul>
        <ul className="navbar-nav ml-auto">
            <li className="nav-item"><a className="nav-link" href="https://twitter.com/oooverflow" target="_blank" rel="noopener noreferrer">OOO</a></li>
            <li className="nav-item"><a className="nav-link" href="https://defcon.org" target="_blank" rel="noopener noreferrer">DEF&nbsp;CON</a></li>
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;
