// frontend/src/index.js
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';      // your App.js code
import './index.css';         // optional, create if you want global styles

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);