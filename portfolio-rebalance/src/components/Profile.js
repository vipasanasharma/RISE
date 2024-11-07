import React, { useState } from "react";
import axios from "axios";

const Profile = () => {
  const [clientId, setClientId] = useState(""); // State for Client ID input
  const [profile, setProfile] = useState({}); // State for profile data
  const [error, setError] = useState(""); // State for error handling
  const [loading, setLoading] = useState(false); // State for loading indicator

  // Function to handle form submission and fetch profile data
  const handleSubmit = (e) => {
    e.preventDefault();
    setError(""); // Clear previous errors
    setProfile({}); // Reset profile data on new request
    setLoading(true); // Start loading

    if (!clientId) {
      setError("Please enter a Client ID.");
      setLoading(false); // Stop loading if no ID is entered
      return;
    }

    axios
      .get("http://localhost:5000/api/profile-data", { params: { 'Client ID': clientId } })
      .then((response) => {
        setProfile(response.data);
        setError(""); // Clear previous errors
      })
      .catch((error) => {
        setError(error.response?.data?.error || "An error occurred while fetching profile data.");
        setProfile({}); // Reset profile data on error
      })
      .finally(() => {
        setLoading(false); // Stop loading after fetch
      });
  };

  return (
    <div>
      <h1>Client Profile</h1>

      {/* Form to input Client ID */}
      <form onSubmit={handleSubmit}>
        <label htmlFor="client-id">Enter Client ID:</label>
        <input
          type="text"
          id="client-id"
          value={clientId}
          onChange={(e) => setClientId(e.target.value)}
        />
        <button type="submit">Submit</button>
      </form>

      {/* Error handling */}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {/* Loading Indicator */}
      {loading && <p>Loading profile data...</p>}

      {/* Display profile data */}
      {!loading && !error && Object.keys(profile).length > 0 ? (
        <div>
          <h2>Profile Details</h2>
          <ul>
            <li>Name: {profile.name || "N/A"}</li>
            <li>Age: {profile.age || "N/A"}</li>
            <li>Client ID: {profile.clientId || "N/A"}</li>
            <li>Risk Tolerance: {profile.riskTolerance || "N/A"}</li>
            <li>Financial Goals: {profile.financialGoals || "N/A"}</li>
          </ul>
        </div>
      ) : (
        !loading && <p>No profile data available. Please check the Client ID.</p>
      )}
    </div>
  );
};

export default Profile;
