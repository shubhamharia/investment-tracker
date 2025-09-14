import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, Plus, RefreshCw, BarChart3, PieChart as PieChartIcon, Home, Menu, X } from 'lucide-react';
import axios from 'axios';
import AddInvestmentModal from './components/AddInvestmentModal';
import PortfolioView from './components/PortfolioView';
import DashboardView from './components/DashboardView';

// Sample data for when API is not available
const samplePortfolioData = [
  { date: '2024-01', value: 50000 },
  { date: '2024-02', value: 52000 },
  { date: '2024-03', value: 48000 },
  { date: '2024-04', value: 55000 },
  { date: '2024-05', value: 58000 },
  { date: '2024-06', value: 62000 },
];

const sampleHoldingsData = [
  { name: 'AAPL', value: 15000, color: '#0088FE', percentage: 24.2 },
  { name: 'GOOGL', value: 12000, color: '#00C49F', percentage: 19.4 },
  { name: 'MSFT', value: 10000, color: '#FFBB28', percentage: 16.1 },
  { name: 'TSLA', value: 8000, color: '#FF8042', percentage: 12.9 },
  { name: 'AMZN', value: 7000, color: '#8884d8', percentage: 11.3 },
  { name: 'Others', value: 10000, color: '#82ca9d', percentage: 16.1 },
];

const samplePlatformData = [
  { platform: 'Interactive Brokers', value: 25000, account_type: 'ISA' },
  { platform: 'Trading 212', value: 20000, account_type: 'Invest' },
  { platform: 'Freetrade', value: 17000, account_type: 'ISA' },
];

const InvestmentTracker = () => {
  const [portfolioData, setPortfolioData] = useState(samplePortfolioData);
  const [dashboardData, setDashboardData] = useState(null);
  const [holdings, setHoldings] = useState(sampleHoldingsData);
  const [platforms, setPlatforms] = useState(samplePlatformData);
  const [loading, setLoading] = useState(false);
  const [showValues, setShowValues] = useState(true);
  const [timeRange, setTimeRange] = useState('1Y');
  const [currentView, setCurrentView] = useState('dashboard');
  const [showAddModal, setShowAddModal] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', id: 'dashboard', icon: Home },
    { name: 'Portfolio', id: 'portfolio', icon: PieChartIcon },
    { name: 'Analytics', id: 'analytics', icon: BarChart3 },
  ];

  // Load dashboard data from API
  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/dashboard');
      setDashboardData(response.data);
      if (response.data.holdings_by_platform) {
        setPlatforms(response.data.holdings_by_platform);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // Use sample data if API is not available
    } finally {
      setLoading(false);
    }
  };

  const handleAddInvestment = (investment) => {
    console.log('Adding investment:', investment);
    // Here you would typically make an API call to add the investment
    // For now, we'll just log it
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const formatCurrency = (value) => {
    if (!showValues) return '*****';
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: 'GBP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value) => {
    if (!showValues) return '*****';
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // Calculate metrics from dashboard data or use sample data
  const totalValue = dashboardData?.portfolio_summary?.total_value || 62000;
  const totalCost = dashboardData?.portfolio_summary?.total_cost || 58000;
  const totalGainLoss = dashboardData?.portfolio_summary?.total_gain_loss || 4000;
  const totalGainLossPct = dashboardData?.portfolio_summary?.total_gain_loss_pct || 6.9;

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile menu overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 flex z-40 md:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
            <div className="absolute top-0 right-0 -mr-12 pt-2">
              <button
                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-6 w-6 text-white" />
              </button>
            </div>
            <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
              <div className="flex-shrink-0 flex items-center px-4">
                <h1 className="text-xl font-bold text-gray-900">Investment Tracker</h1>
              </div>
              <nav className="mt-5 px-2 space-y-1">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        setCurrentView(item.id);
                        setSidebarOpen(false);
                      }}
                      className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full ${
                        currentView === item.id
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                    >
                      <Icon className="mr-3 h-5 w-5" />
                      {item.name}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:flex-shrink-0">
        <div className="flex flex-col w-64">
          <div className="flex flex-col h-0 flex-1 border-r border-gray-200 bg-white">
            <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
              <div className="flex items-center flex-shrink-0 px-4">
                <h1 className="text-xl font-bold text-gray-900">Investment Tracker</h1>
              </div>
              <nav className="mt-5 flex-1 px-2 space-y-1">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setCurrentView(item.id)}
                      className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full ${
                        currentView === item.id
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }`}
                    >
                      <Icon className="mr-3 h-5 w-5" />
                      {item.name}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div className="flex items-center">
                <button
                  className="md:hidden mr-4"
                  onClick={() => setSidebarOpen(true)}
                >
                  <Menu className="h-6 w-6 text-gray-600" />
                </button>
                <div>
                  <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                    {navigation.find(nav => nav.id === currentView)?.name || 'Dashboard'}
                  </h1>
                  <p className="text-gray-600">Track and manage your investments</p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setShowValues(!showValues)}
                  className="flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  {showValues ? (
                    <>
                      <EyeOff className="h-4 w-4 mr-2" />
                      Hide Values
                    </>
                  ) : (
                    <>
                      <Eye className="h-4 w-4 mr-2" />
                      Show Values
                    </>
                  )}
                </button>
                <button
                  onClick={loadDashboardData}
                  disabled={loading}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
                <button 
                  onClick={() => setShowAddModal(true)}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Investment
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {currentView === 'dashboard' && (
              <DashboardView 
                dashboardData={dashboardData}
                portfolioData={portfolioData}
                holdings={holdings}
                platforms={platforms}
                showValues={showValues}
                timeRange={timeRange}
                setTimeRange={setTimeRange}
                formatCurrency={formatCurrency}
                formatPercentage={formatPercentage}
                totalValue={totalValue}
                totalCost={totalCost}
                totalGainLoss={totalGainLoss}
                totalGainLossPct={totalGainLossPct}
              />
            )}
            {currentView === 'portfolio' && <PortfolioView />}
            {currentView === 'analytics' && (
              <div className="text-center py-12">
                <BarChart3 className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">Analytics Coming Soon</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Advanced analytics and performance metrics will be available here.
                </p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Add Investment Modal */}
      <AddInvestmentModal 
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddInvestment}
      />
    </div>
  );
};

export default InvestmentTracker;
