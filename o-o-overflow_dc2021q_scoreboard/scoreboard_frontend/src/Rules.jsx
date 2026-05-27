import React from "react";

function Rules() {
  return (
    <div className="rulespage">

      <h2>Rules Philosophy</h2>
      <p>
        Our goal is to run a challenging CTF that is as fair as possible. In that spirit, we present the rules, with the goal of keeping things fair, and hopefully fun. 
      </p>
      <p>
        We hope that you play with the spirit of competition and adopt a competitive, fair play, and positive sports(person/man/women)ship attitude. 
      </p>

      <h2>Basic Rules</h2>
      <ul>
        <li>
          No Denial of Service—DoS is super lame, don't do it or you will be
          banned
        </li>
        <li>No sharing flags, exploits, or hints—Do your own hacks</li>
        <li>
          No attacks against our infrastructure—Hack the challenges, not us
        </li>
        <li>No automated scanning—For these challenges, do better</li>
      </ul>

      <h2>Scoring</h2>
      <p>
        We do adaptive scoring based on the number of solves:
        starting at 500 and decreasing from there (based on the total number of
        teams that solved the challenge).
      </p><p>We{" "}
        <a href="https://github.com/o-o-overflow/scoring-playground">
          released a scoring playground
        </a>{" "}
        so that teams with questions or concerns about the exact scoring
        algorithm can see how that affects the overall ranking.
          </p>

      <h2>Challenge Release Schedule</h2>
      <p>
        We will release challenges throughout the competition as we see fit. We base these decisions on the flow of the game and the availability of the humans that wrote the challenge. We will not release any challenges less than 12 hours to the end of the competition (except for patches for shortcut solutions). 
      </p>

      <h2>Shortcut Solutions</h2>
      <p>
        We strive to develop challenges that stretch and test everyone's skills. We also test the challenges to ensure that there's ~one intended path/solution. 
      </p>
      <p>
        Unfortunately, we are human and mistakes happen. Our policy will be: if we see that a challenge has been solved within what we consider to be a short time from launch by a "shortcut solution", then we might release an updated version. 
      </p>
      <h2>Flag Format</h2>
      <p>
        Unless otherwise noted, all flags will be in the format: <code>OOO&#123;…&#125;</code>
      </p>
      <p>
        <strong>
          <em>
            NOTE: You must submit the whole thing, including the{" "}
            <code>OOO&#123;…&#125;</code>.
          </em>
        </strong>
      </p>

      <h2>Flag Location</h2>
      <p>
        Unless otherwise noted in the challenge description, all flags will be located at: <code>/flag</code>
      </p>

      <h2>Proof of Work (POW)</h2>
      <p>
        We may implement a POW in front of a challenge if we feel it is
        necessary.
        </p><p>
        Please don't make it necessary
      </p>

      <h2>Hints</h2>
      <p>
        Do not expect hints. Particularly if a service is already pwned, it
        would be unfair to give one team a hint when it's already solved.
      </p><p>We do appreciate issue reports and if we
        feel that something is significantly wrong, then we will update the
        description and tweet about it. If you straight up ask for hints on 
        Discord, expect to be referred to this page.
          </p>

      <p>
        The one exception to this rule is any challenge marked with
        the tag <code>easy</code>. These challenges are (in our
        estimation) on the easy side, and we will hint and help people
        on these challenges. There will only be a few challenges
        marked <code>easy</code>.
      </p>

      <h2>
        Twitter and Discord
      </h2>
      <p>
        <b>All game announcements will be made through our Twitter account{" "}
        <a href="https://twitter.com/oooverflow">@oooverflow</a></b>
      </p>
      <p>
        Times change, and we must change with them.
        We're using the official DEF CON
        discord <a href="https://discord.gg/defcon">discord.gg/defcon</a>.
        You should hang out with us in the CTF area.
      </p>

      <h2>Flag Submission Delay</h2>
      <p>Flags can be submitted once every 30 seconds per challenge.</p>

      <h2>Team Size</h2>
      <p>There is no limit on team sizes.</p>

      <h2>Public pcaps</h2>
      <p>We collect pcaps for almost all challenges. They will be relased after the game, anonymized.</p>
      <p>You can find your own traffic (after the fact).
        To do so, during the game, run <code>nc -v my-pcap-ip.oooverflow.io 5000</code></p>
      <p>If you use multiple IPs to connect to the game, remember to run that command from all of them.</p>


      <h2>Info on prequals, etc.</h2>
      <p>See <a href="https://oooverflow.io/dc-ctf-2021-quals/">our main website</a>.</p>

      <h2>Who are you anyway?</h2>
      <p>We are the Order of the Overflow. We are the current host of <a href="https://www.defcon.org/html/links/dc-ctf.html">DEF CON CTF</a> (Quals and Finals).</p>
      <p>Info about us and our philosophy is <a href="https://oooverflow.io/philosophy.html">here</a> and we're reachable at <a href="mailto:team@oooverflow.io">team@oooverflow.io</a>.</p>

      <h2>OMG I'm insanely confused</h2>
      <p>It's a hacking competition, and the DEF CON CTF is a hard one at that.</p>
      <p>You might want to start with something easier, maybe from our <a href="https://archive.ooo">archive</a> -- <a href="https://github.com/o-o-overflow/archiveooo/wiki/FAQ">more info</a> or <a href="https://pwn.college">start your hacking journey at pwn.college</a>.</p>
    </div>
  );
}
export default Rules;
