import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

const CodeMemory = () => {
  const [memoryStats, setMemoryStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMemoryStats();
  }, []);

  const fetchMemoryStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/memory/stats`);
      const data = await response.json();
      setMemoryStats(data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch memory stats:', err);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Code Memory</h1>
      
      {memoryStats && memoryStats.stats ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm mb-2">Bug Patterns</h3>
            <p className="text-3xl font-bold text-red-400">
              {memoryStats.stats.bug_patterns || 0}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm mb-2">Architecture Patterns</h3>
            <p className="text-3xl font-bold text-blue-400">
              {memoryStats.stats.architecture || 0}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm mb-2">Algorithms</h3>
            <p className="text-3xl font-bold text-green-400">
              {memoryStats.stats.algorithms || 0}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm mb-2">Projects</h3>
            <p className="text-3xl font-bold text-purple-400">
              {memoryStats.stats.projects || 0}
            </p>
          </div>
        </div>
      ) : (
        <p className="text-gray-400">No memory data available</p>
      )}
      
      <div className="mt-8 bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">About Code Memory</h2>
        <p className="text-gray-400">
          JARVIS learns from every project build, storing:
        </p>
        <ul className="list-disc list-inside text-gray-400 mt-2 space-y-1">
          <li>Bug patterns to avoid in future projects</li>
          <li>Architecture performance data for better recommendations</li>
          <li>Algorithm implementations and their efficiency</li>
          <li>Project outcomes and lessons learned</li>
        </ul>
      </div>
    </div>
  );
};

export default CodeMemory;
