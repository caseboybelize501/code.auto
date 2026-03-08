import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

const DevDashboard = () => {
  const [systemProfile, setSystemProfile] = useState(null);
  const [memoryStats, setMemoryStats] = useState(null);
  const [requirements, setRequirements] = useState('');
  const [isBuilding, setIsBuilding] = useState(false);
  const [currentProject, setCurrentProject] = useState(null);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);

  // Fetch system profile on mount
  useEffect(() => {
    fetchSystemProfile();
    fetchMemoryStats();
  }, []);

  const fetchSystemProfile = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/system/profile`);
      const data = await response.json();
      setSystemProfile(data);
    } catch (err) {
      console.error('Failed to fetch system profile:', err);
    }
  };

  const fetchMemoryStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/memory/stats`);
      const data = await response.json();
      setMemoryStats(data);
    } catch (err) {
      console.error('Failed to fetch memory stats:', err);
    }
  };

  const handleStartProject = async (e) => {
    e.preventDefault();
    if (!requirements.trim()) return;

    setIsBuilding(true);
    setError(null);
    setLogs([{ type: 'info', message: 'Starting project...', timestamp: new Date().toISOString() }]);

    try {
      const response = await fetch(`${API_BASE}/api/project/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ requirements }),
      });

      const data = await response.json();
      setCurrentProject(data);
      
      // Log the process
      addLog('info', `Project ID: ${data.project_id}`);
      
      if (data.plan) {
        addLog('success', `Architecture: ${data.plan.architecture}`);
        addLog('success', `Language: ${data.plan.language}, Framework: ${data.plan.framework}`);
      }
      
      if (data.files) {
        addLog('success', `Generated ${data.files.length} files`);
      }
      
      if (data.test_results) {
        const status = data.test_results.passed ? 'passed' : 'failed';
        addLog(status === 'passed' ? 'success' : 'error', `Tests ${status}`);
      }
      
      if (data.build_result) {
        const status = data.build_result.success ? 'success' : 'failed';
        addLog(status === 'success' ? 'success' : 'error', `Build ${status} (${data.build_result.build_time}s)`);
      }
      
      if (data.deployment) {
        if (data.deployment.success) {
          addLog('success', `Deployed to ${data.deployment.url}`);
        } else {
          addLog('warning', 'Deployment skipped (Docker not available)');
        }
      }
      
      if (data.metrics) {
        addLog('info', `Latency: ${data.metrics.latency}, Throughput: ${data.metrics.throughput}`);
      }

      setIsBuilding(false);
      fetchMemoryStats();
    } catch (err) {
      setError(err.message);
      addLog('error', `Error: ${err.message}`);
      setIsBuilding(false);
    }
  };

  const addLog = (type, message) => {
    setLogs(prev => [...prev, { type, message, timestamp: new Date().toISOString() }]);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-500';
      case 'completed_with_issues': return 'text-yellow-500';
      case 'failed': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getLogColor = (type) => {
    switch (type) {
      case 'success': return 'text-green-400';
      case 'error': return 'text-red-400';
      case 'warning': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center">
          🤖 JARVIS Development Dashboard
        </h1>

        {/* System Status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2">System Status</h3>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></div>
              <span className="text-green-400">Online</span>
            </div>
            {systemProfile && (
              <p className="text-sm text-gray-400 mt-2">
                {Object.keys(systemProfile.toolchain?.compilers || {}).length} compilers detected
              </p>
            )}
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2">Memory Store</h3>
            {memoryStats ? (
              <div className="space-y-1 text-sm">
                {Object.entries(memoryStats.stats || {}).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-400 capitalize">{key}:</span>
                    <span className="text-blue-400">{value}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400">Loading...</p>
            )}
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2">Active Projects</h3>
            <p className="text-3xl font-bold text-blue-400">
              {currentProject ? '1' : '0'}
            </p>
          </div>
        </div>

        {/* Project Input */}
        <div className="bg-gray-800 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Start New Project</h2>
          <form onSubmit={handleStartProject}>
            <textarea
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder="Describe your project requirements... (e.g., 'Build a REST API for a todo application with user authentication')"
              className="w-full bg-gray-700 rounded-lg p-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
              disabled={isBuilding}
            />
            <button
              type="submit"
              disabled={isBuilding || !requirements.trim()}
              className="mt-4 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg font-semibold transition-colors"
            >
              {isBuilding ? '🔄 Building...' : '🚀 Start Project'}
            </button>
          </form>
        </div>

        {/* Build Logs */}
        {logs.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">Build Logs</h2>
            <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm max-h-64 overflow-y-auto">
              {logs.map((log, index) => (
                <div key={index} className={`${getLogColor(log.type)} mb-1`}>
                  <span className="text-gray-500">[{new Date(log.timestamp).toLocaleTimeString()}]</span>{' '}
                  {log.message}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Project Results */}
        {currentProject && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Project Info */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">
                Project Results
                <span className={`ml-3 ${getStatusColor(currentProject.status)}`}>
                  {currentProject.status}
                </span>
              </h2>
              
              {currentProject.plan && (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Architecture:</span>
                    <span>{currentProject.plan.architecture}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Language:</span>
                    <span>{currentProject.plan.language}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Framework:</span>
                    <span>{currentProject.plan.framework}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Files Generated:</span>
                    <span>{currentProject.files?.length || 0}</span>
                  </div>
                </div>
              )}

              {currentProject.metrics && (
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <h3 className="font-semibold mb-2">Performance Metrics</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-400">Latency:</span>
                      <span className="ml-2">{currentProject.metrics.latency}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Throughput:</span>
                      <span className="ml-2">{currentProject.metrics.throughput}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">CPU:</span>
                      <span className="ml-2">{currentProject.metrics.cpu_usage}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Memory:</span>
                      <span className="ml-2">{currentProject.metrics.memory_usage}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Test Results */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Test Results</h2>
              {currentProject.test_results ? (
                <div className="space-y-2">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-2 ${
                      currentProject.test_results.passed ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <span>
                      {currentProject.test_results.passed ? 'All tests passed' : 'Some tests failed'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-400">
                    Coverage: {currentProject.test_results.coverage}%
                  </div>
                  {currentProject.test_results.test_count > 0 && (
                    <div className="text-sm text-gray-400">
                      Tests: {currentProject.test_results.test_count}
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-gray-400">No test results available</p>
              )}

              {currentProject.build_result && (
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-2 ${
                      currentProject.build_result.success ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <span>Build {currentProject.build_result.success ? 'successful' : 'failed'}</span>
                  </div>
                  <div className="text-sm text-gray-400 mt-1">
                    Build time: {currentProject.build_result.build_time}s
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mt-6 bg-red-900/50 border border-red-500 rounded-lg p-4">
            <h3 className="text-red-400 font-semibold">Error</h3>
            <p className="text-red-300 mt-1">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DevDashboard;
