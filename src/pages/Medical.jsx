import "./Form.css";
import { Link } from "react-router-dom";
import { useState } from "react";
import SubmissionResult from "../components/SubmissionResult";

function Medical(){

    const [injured, setInjured] = useState("")
    const [severity, setSeverity] = useState("Minor")
    const [conscious, setConscious] = useState("Unknown");
    const [breathing, setBreathing] = useState("Unknown");
    const [location, setLocation] = useState("");
    const [submissionStatus, setSubmissionStatus] = useState(null);

    function handleSubmit() {

        if (Number(injured) <= 0) {
            alert("Please enter a valid number of injured people.");
            return;
        }

        if (location.trim() === "") {
            alert("Please enter an approximate location.");
            return;
        }

        const request = {
            injured,
            severity,
            conscious,
            breathing,
            location
        };

        console.log("Medical Request:", request);

        setSubmissionStatus("received");

        // Reset the form
        setInjured("");
        setSeverity("Minor");
        setConscious("Unknown");
        setBreathing("Unknown");
        setLocation("");
}

if (submissionStatus) {
    return (
        <div className="page-container">

            <SubmissionResult
                status={submissionStatus}
                onReset={() => {
                    setSubmissionStatus(null);
                    setInjured("");
                    setSeverity("Minor");
                    setConscious("Unknown");
                    setBreathing("Unknown");
                    setLocation("");
                }}
            />

        </div>
    );
}

    return (
        <div className="page-container">

            <header className="page-header">
                <h1 className="page-title">Medical Assistance</h1>

                <p className="page-description">
                    Describe your medical emergency below. Critical requests
                    should be submitted as soon as possible.
                </p>
            </header>

            <div className="form-card">

                <div className="form-group">
                    <label htmlFor="injured">
                        How many people are injured?
                    </label>

                    <input
                        id="injured"
                        type="number"
                        min="1"
                        value={injured}
                        onChange={(event) => setInjured(event.target.value)}
                        placeholder="Number of injured people"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="conscious">
                        Are the injured conscious?
                    </label>

                    <select
                        id="conscious"
                        value={conscious}
                        onChange={(event) => setConscious(event.target.value)}
                    >
                        <option>Yes</option>
                        <option>No</option>
                        <option>Unknown</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="breathing">
                        Are they breathing?
                    </label>

                    <select
                        id="breathing"
                        value={breathing}
                        onChange={(event) => setBreathing(event.target.value)}
                    >
                        <option>Yes</option>
                        <option>No</option>
                        <option>Unknown</option>
                    </select>
                </div>

                <div className="form-group">
                    <label htmlFor="location">
                        Approximate Location
                    </label>

                    <input
                        id="location"
                        type="text"
                        value={location}
                        onChange={(event) => setLocation(event.target.value)}
                        placeholder="Example: Apartment 204, second floor"
                    />
                </div>

                <div className="form-actions">
                    <button
                        className="submit-button"
                        onClick={handleSubmit}
                        disabled={injured === "" || location.trim() === ""}
                    >
                        Submit Medical Request
                    </button>

                    <Link to="/" className="back-button">
                        Back to Home
                    </Link>
                </div>

            </div>
        </div>
    );
}

export default Medical;