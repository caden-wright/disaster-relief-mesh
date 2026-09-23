import { useState } from "react";
import { Link } from "react-router-dom";
import "./Form.css";
import SubmissionResult from "../components/SubmissionResult";
import { submitMessage } from "../api/helpPoint";

function CheckIn() {
    const [people, setPeople] = useState("1");
    const [submissionStatus, setSubmissionStatus] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    async function handleSubmit() {
        if (Number(people) <= 0) {
            alert("Please enter a valid number of people.");
            return;
        }

        const request = {
            type: "safety_checkin",
            status: "safe",
            people: Number(people)
        };

        setSubmitting(true);

        try {
            const result = await submitMessage(request);
            setSubmissionStatus(result.status);
        } catch (error) {
            console.error("Safety Check-In failed:", error);
            setSubmissionStatus("error");
        } finally {
            setSubmitting(false);
        }
    }

    if (submissionStatus) {
        return (
            <div className="page-container">
                <SubmissionResult
                    status={submissionStatus}
                    onReset={() => {
                        setSubmissionStatus(null);
                        setPeople("1");
                    }}
                />
            </div>
        );
    }

    return (
        <div className="page-container">
            <header className="page-header">
                <h1 className="page-title">Safety Check-In</h1>
                <p className="page-description">
                    Let emergency coordinators know that you and your
                    group are safe at this Help Point.
                </p>
            </header>

            <div className="form-card">
                <div className="status-confirmation">
                    <span className="safe-icon">✓</span>

                    <div>
                        <strong>Status: Safe</strong>
                        <p>
                            This check-in reports that your group is currently safe.
                        </p>
                    </div>
                </div>

                <div className="form-group">
                    <label htmlFor="people">Number of People</label>
                    <input
                        id="people"
                        type="number"
                        min="1"
                        value={people}
                        onChange={(event) => setPeople(event.target.value)}
                    />
                </div>

                <div className="form-actions">
                    <button
                        className="submit-button"
                        onClick={handleSubmit}
                        disabled={people === "" || submitting}
                    >
                        {submitting ? "Submitting..." : "Submit Safety Check-In"}
                    </button>

                    <Link to="/" className="back-button">
                        Back to Home
                    </Link>
                </div>
            </div>
        </div>
    );
}

export default CheckIn;
