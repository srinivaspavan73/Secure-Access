import React, { useState, useCallback, useRef, useEffect } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import './WebcamCapture.css';

const WebcamCapture = () => {
    const webcamRef = useRef(null);
    const [image, setImage] = useState('');
    const [instruction, setInstruction] = useState('Please press Start to begin verification');
    const [nextStep, setNextStep] = useState('');
    const [matchedName, setMatchedName] = useState(''); // Added state variable for matched name
    // Initial Capture and Display Matched Name
    const captureAndMatchFace = useCallback(async () => {
        const imageSrc = webcamRef.current.getScreenshot();
        setImage(imageSrc);

        try {
            const response = await axios.post('http://127.0.0.1:5000/process-image', { image: imageSrc });
            console.log(response.data);
            if (response.data.names && response.data.names.length > 0) {
                setMatchedName(response.data.names.join(', '));
                // Optionally start verification here or wait for user action
            } else {
                setInstruction("No faces detected, please try again.");
            }
        } catch (error) {
            console.error('Error sending image to server:', error);
        }
    }, [webcamRef]);

    const startVerification = useCallback(async () => {
        try {
            const response = await axios.post('http://127.0.0.1:5000/start-verification');
            console.log(response.data);
            setInstruction(response.data.message);
            setNextStep(response.data.nextStep);
        } catch (error) {
            console.error('Error starting verification:', error);
        }
        // Starting verification logic as before
    }, []);
    const verifyOrientation = useCallback(async () => {
        const imageSrc = webcamRef.current.getScreenshot();
        setImage(imageSrc);
    
        try {
            const response = await axios.post('http://127.0.0.1:5000/verify-orientation', {
                image: imageSrc,
                step: nextStep
            });
            console.log(response.data);
            if (response.data.instruction === "No person detected") {
                setInstruction(response.data.message); // Display "No person detected" message
                setNextStep('initial'); // Reset to initial step to restart the process
            } else {
                setInstruction(response.data.instruction);
                setNextStep(response.data.nextStep);
            }
        } catch (error) {
            console.error('Error verifying orientation:', error);
        }
    }, [nextStep, webcamRef]);
    useEffect(() => {
        startVerification();
    }, [startVerification]);

    return (
        <div className="webcam-container">
            <Webcam ref={webcamRef} screenshotFormat="image/jpeg" />
            <button onClick={captureAndMatchFace}>Start Face Verification</button>
            {matchedName && <p>Matched Name: {matchedName}</p>}
            {/* Display the instruction or next step based on your process flow */}
            {nextStep && <button onClick={verifyOrientation}>{instruction}</button>}
            {image && <img src={image} alt="Captured" style={{ display: 'none' }} />}
        </div>
    );
};

export default WebcamCapture;