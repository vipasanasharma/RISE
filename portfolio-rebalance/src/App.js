import React from "react";
import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";
import Homepage from "./components/Homepage";
import Profile from "./components/Profile";
import Nudge from "./components/Nudge";

function App() {
  return (
    <Router>
      <div className="App">
        <h1>Financial Dashboard</h1>

        {/* Navigation Menu */}
        <nav>
          <ul>
            <li>
              <Link to="/">Home</Link>
            </li>
            <li>
              <Link to="/profile">Profile</Link>
            </li>
            <li>
              <Link to="/nudge">Nudge</Link>
            </li>
          </ul>
        </nav>

        {/* Routes for different components */}
        <Routes>
          <Route path="/" element={<Homepage />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/nudge" element={<Nudge />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
