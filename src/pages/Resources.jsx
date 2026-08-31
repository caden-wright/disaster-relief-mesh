import { useState } from "react";
import { Link } from "react-router-dom";
import "./Form.css";
import SubmissionResult from "../components/SubmissionResult";

function Resources() {

    const [resource, setResource] = useState("Water");
    const [people, setPeople] = useState("1");
    const [urgency, setUrgency] = useState("Normal");
    const [submissionStatus, setSubmissionStatus] = useState(null);

    function handleSubmit() {

        if (Number(people) <= 0) {
            alert("Please enter a valid number of people.");
            return;
        }

        const request = {
            type: "resource_request",
            resource,
            people: Number(people),
            urgency
        };

        console.log("Resource Request:", request);

        setSubmissionStatus("received");

        setResource("Water");
        setPeople("1");
        setUrgency("Normal");
    }

    if (submissionStatus) {
    return (
        <div className="page-container">

            <SubmissionResult
                status={submissionStatus}
                onReset={() => {
                    setSubmissionStatus(null);
                    setResource("Water");
                    setPeople("1");
                    setUrgency("Normal");
                }}
            />

        </div>
    );
}

    return (
        <div className="page-container">

            <header className="page-header">
                <h1 className="page-title">
                    Request Resources
                </h1>

                <p className="page-description">
                    Select the resource your group currently needs.
                </p>
            </header>

            <div className="form-card">

                <div className="form-group">

                    <label>
                        Resource Needed
                    </label>

                    <div
                        className="resource-options"
                        role="radiogroup"
                        aria-label="Resource needed"
                    >

                        {["Water", "Food", "Medicine", "Shelter"].map(
                            (option) => (
                                <button
                                    key={option}
                                    type="button"
                                    className={
                                        resource === option
                                            ? "resource-option selected"
                                            : "resource-option"
                                    }
                                    onClick={() => setResource(option)}
                                    role="radio"
                                    aria-checked={resource === option}
                                >
                                    {option}
                                </button>
                            )
                        )}

                    </div>

                </div>

                <div className="form-group">
                    <label htmlFor="people">
                        Number of People
                    </label>

                    <input
                        id="people"
                        type="number"
                        min="1"
                        value={people}
                        onChange={(event) =>
                            setPeople(event.target.value)
                        }
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="urgency">
                        Urgency
                    </label>

                    <select
                        id="urgency"
                        value={urgency}
                        onChange={(event) =>
                            setUrgency(event.target.value)
                        }
                    >
                        <option>Normal</option>
                        <option>High</option>
                    </select>
                </div>

                <div className="form-actions">

                    <button
                        className="submit-button"
                        onClick={handleSubmit}
                        disabled={people === ""}
                    >
                        Submit Resource Request
                    </button>

                    <Link to="/" className="back-button">
                        Back to Home
                    </Link>

                </div>

            </div>

        </div>
    );
}

export default Resources;