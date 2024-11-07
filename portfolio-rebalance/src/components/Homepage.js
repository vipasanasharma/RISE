import React, { useState } from "react";
import axios from "axios";

const Homepage = () => {
  const [clientId, setClientId] = useState(""); // State for Client ID
  const [data, setData] = useState({ goals: {}, debt: {}, assetAllocation: {} });
  const [error, setError] = useState(""); // State for handling errors
  const [loading, setLoading] = useState(false); // State for loading indicator

  // Fetch data when the client submits the Client ID
  const handleSubmit = (e) => {
    e.preventDefault();
    setError(""); // Clear any previous error
    setData({ goals: {}, debt: {}, assetAllocation: {} }); // Reset data on new request
    setLoading(true); // Set loading to true

    if (!clientId) {
      setError("Please enter a Client ID.");
      setLoading(false); // Reset loading state
      return;
    }

    axios
      .get(`http://localhost:5000/api/homepage-data`, { params: { 'Client ID': clientId } })
      .then((response) => {
        setData(response.data);
        setError(""); // Clear any previous error
      })
      .catch((error) => {
        setError(error.response?.data?.error || "An error occurred while fetching data.");
        setData({ goals: {}, debt: {}, assetAllocation: {} }); // Reset data in case of an error
      })
      .finally(() => {
        setLoading(false); // Reset loading state after fetch
      });
  };

  return (
    <div>
      <h1>Client Homepage</h1>

      {/* Form to take Client ID */}
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
      {loading && <p>Loading data...</p>}

      {/* Display the data */}
      {!loading && !error && (
        <>
          <h2>Goals</h2>
          {Object.keys(data.goals).length === 0 ? (
            <p>No goals available for this client.</p>
          ) : (
            <ul>
              <li>Retirement Corpus: {data.goals.retirementCorpus || "N/A"}</li>
              <li>Child Education: {data.goals.childEducation || "N/A"}</li>
              <li>Property Purchase: {data.goals.propertyPurchase || "N/A"}</li>
            </ul>
          )}

          <h2>Debt</h2>
          <p>Total Debt: {data.debt.totalDebt || "N/A"}</p>

          <h2>Asset Allocation</h2>
          {Object.keys(data.assetAllocation).length === 0 ? (
            <p>No asset allocation data available.</p>
          ) : (
            <ul>
              <li>Equity: {data.assetAllocation.equity || "N/A"}</li>
              <li>Real Estate: {data.assetAllocation.realEstate || "N/A"}</li>
              <li>Corporate Bonds: {data.assetAllocation.corporateBonds || "N/A"}</li>
              <li>Government Bonds: {data.assetAllocation.governmentBonds || "N/A"}</li>
            </ul>
          )}
        </>
      )}
    </div>
  );
};

export default Homepage;
