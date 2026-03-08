import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

const RuntimeMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/system/profile`);
      const data = await response.json();
      setMetrics(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
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
      <h1 className="text-2xl font-bold mb-6">Runtime Metrics</h1>
      
      {metrics ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm mb-2">Compilers</h3>
            <p className="text-2xl font-bold">
              {Object.keys(metrics.toolchain?.compilers || {}).length}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm mb-2">Build Systems</h3>
            <p className="text-2xl font-bold">
              {metrics.toolchain?.build_systems?.length || 0}
            </p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-gray-400 text-sm mb-2">Package Managers</h3>
            <p className="text-2xl font-bold">
              {metrics.toolchain?.package_managers?.length || 0}
            </p>
          </div>
        </div>
      ) : (
        <p className="text-gray-400">No metrics available</p>
      )}
    </div>
  );
};

export default RuntimeMetrics;
