import React, { useState } from 'react';

const TestResults = () => {
  const [testResults, setTestResults] = useState(null);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Test Results</h1>
      
      <div className="bg-gray-800 rounded-lg p-6">
        <p className="text-gray-400">
          Test results are displayed in the main dashboard after running a project build.
        </p>
      </div>
    </div>
  );
};

export default TestResults;
