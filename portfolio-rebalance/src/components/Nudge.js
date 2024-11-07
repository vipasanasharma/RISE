import React, { useState } from "react";

const Nudge = () => {
  const [clientId, setClientId] = useState("");
  const [nudgeData, setNudgeData] = useState({
    projectionsBefore: {},
    projectionsAfter: {},
    nudgeMessage: "",
    fullResponse: "",
  });
  const [error, setError] = useState("");
  const [isProcessingWeek, setIsProcessingWeek] = useState(false);
  const [currentWeek, setCurrentWeek] = useState(1);
  const [totalWeeks, setTotalWeeks] = useState(0);
  const [decisionPending, setDecisionPending] = useState(false);
  
  // Additional state to hold LLM output
  const [llmOutput, setLlmOutput] = useState("");
  const [projectionsAfter, setprojectionsAfter] = useState("");


  const handleSubmit = (e) => {
    e.preventDefault();
    if (!clientId) {
      setError("Please enter a Client ID.");
      return;
    }

    setError("");
    setIsProcessingWeek(false);
    setNudgeData({
      projectionsBefore: {},
      projectionsAfter: {},
      nudgeMessage: "",
      fullResponse: "",
    });
    setCurrentWeek(259); // Reset to the first week
    fetchWeekData(clientId, 259); // Fetch data for the first week
  };

  const fetchWeekData = (clientId, week) => {
    setIsProcessingWeek(true);
    setDecisionPending(false);

    fetch(`http://localhost:5000/api/nudge-data?Client+ID=${clientId}&week=${week}`)
      .then((response) => {
        console.log("Response Status:", response); // Log response status
        return response.json()
      })
      .then((data) => {
        console.log("Received data from backend:", data);
        setLlmOutput(data)
        setprojectionsAfter(data)
        const { llm_response, projections_after_data } = data;
      
      // Do something with the response and projections_after_data
      console.log("Response:", llm_response);
      console.log("Projections after data:", projections_after_data);
        
        // Validate data before setting state
        if (data && data.projectionsBefore && data.projectionsAfter) {
          const projectionsBefore = data.projectionsBefore || {};
          const projectionsAfter = data.projectionsAfter || {};
          const nudgeMessage = data.nudgeMessage || "";

          const fullResponse = `
            Current Week: ${week}
            Projections Before: ${JSON.stringify(projectionsBefore, null, 2)}
            Projections After: ${JSON.stringify(projectionsAfter, null, 2)}
            Suggested Nudge: ${nudgeMessage}
          `;

          setNudgeData({
            projectionsBefore,
            projectionsAfter,
            nudgeMessage,
            fullResponse,
          });
          setTotalWeeks(data.totalWeeks); // Get total number of weeks from response
          console.log("Total Weeks:", data.totalWeeks); // Log total weeks
          setIsProcessingWeek(false);
          setDecisionPending(true); // Prompt user for a decision after LLM finishes for the week
          setLlmOutput(fullResponse); // Set LLM output
        } else {
          console.error("Invalid data structure received:", data);
          setError("Invalid data structure received.");
          setIsProcessingWeek(false);
        }
      })
      .catch((error) => {
        console.error("API Error:", error);
        setError("An error occurred while fetching nudge data.");
        setIsProcessingWeek(false);
      });
  };

  const handleYes = () => {
    fetch("http://localhost:5000/api/update-excel", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        clientId: clientId,
        week: currentWeek,
        updatedProjections: nudgeData.projectionsAfter,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Excel Updated:", data);
        proceedToNextWeek(); // After updating Excel, move to the next week
      })
      .catch((error) => {
        console.error("Error updating Excel:", error);
        alert("An error occurred while updating Excel.");
      });
  };

  const handleNo = () => {
    proceedToNextWeek(); // Simply move to the next week without updating Excel
  };

  const proceedToNextWeek = () => {
    if (currentWeek < totalWeeks) {
      setCurrentWeek(currentWeek + 1); // Move to next week
      fetchWeekData(clientId, currentWeek + 1); // Fetch data for the next week
    } else {
      alert("All weeks processed.");
      setDecisionPending(false); // No more decisions to be made
    }
  };

  return (
    <div>
      <h1>Nudge Data</h1>
      <form onSubmit={handleSubmit}>
        <label htmlFor="client-id">Enter Client ID:</label>
        <input
          type="text"
          id="client-id"
          value={clientId}
          onChange={(e) => setClientId(e.target.value)}
        />
        <button type="submit" disabled={isProcessingWeek}>
          Submit
        </button>
      </form>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {isProcessingWeek && <p>Processing week {currentWeek}...</p>}

      {!isProcessingWeek && (
        <div>
          <h2>Nudge Details (Week {currentWeek})</h2>
          <h3>Projections Before</h3>
          <ul>
            <li>Equity: {nudgeData.projectionsBefore.Equity}</li>
            <li>Real Estate: {nudgeData.projectionsBefore["Real Estate"]}</li>
            <li>Corporate Bonds: {nudgeData.projectionsBefore.CorporateBonds}</li>
            <li>Government Bonds: {nudgeData.projectionsBefore.GovernmentBonds}</li>
          </ul>

          <h3>Projections After</h3>
          <ul>
            <li>Equity: {nudgeData.projectionsAfter.Equity}</li>
            <li>Real Estate: {nudgeData.projectionsAfter["Real Estate"]}</li>
            <li>Corporate Bonds: {nudgeData.projectionsAfter.CorporateBonds}</li>
            <li>Government Bonds: {nudgeData.projectionsAfter.GovernmentBonds}</li>
          </ul>

          <h3>Suggested Nudge</h3>
          <p>{nudgeData.nudgeMessage}</p>


          {decisionPending && (
            <div>
              <button onClick={handleYes} style={{ marginRight: "10px" }}>
                Yes, Update Excel
              </button>
              <button onClick={handleNo}>No, Reject Nudge</button>
            </div>
          )}

          <h3>Full LLM Response</h3>
          <textarea
            value={llmOutput.llm_response} // Display the full LLM response
            readOnly
            style={{
              width: "100%",
              height: "300px",
              whiteSpace: "pre-wrap",
              overflowY: "scroll",
            }}
          />


          <h3>Full LLM Response</h3>
          <textarea
            value={projectionsAfter.projections_after_data} // Display the full LLM response
            readOnly
            style={{
              width: "100%",
              height: "300px",
              whiteSpace: "pre-wrap",
              overflowY: "scroll",
            }}
          />


          
        </div>
      )}
    </div>
  );
};

export default Nudge;
