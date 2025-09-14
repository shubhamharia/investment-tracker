import React, { useState, useEffect } from 'react';
import { Search, Filter, SortAsc, SortDesc, TrendingUp, TrendingDown } from 'lucide-react';

const PortfolioView = () => {
  const [portfolios, setPortfolios] = useState([]);
  const [holdings, setHoldings] = useState([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('value');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterPlatform, setFilterPlatform] = useState('all');

  // Sample data
  const samplePortfolios = [
    { id: 1, name: 'Main Portfolio', total_value: 62000, total_cost: 58000, currency: 'GBP' },
    { id: 2, name: 'ISA Portfolio', total_value: 25000, total_cost: 23000, currency: 'GBP' },
    { id: 3, name: 'SIPP Pension', total_value: 45000, total_cost: 42000, currency: 'GBP' },
  ];

  const sampleHoldings = [
    {
      id: 1,
      security: { symbol: 'AAPL', name: 'Apple Inc.' },
      platform: { name: 'Interactive Brokers', account_type: 'ISA' },
      quantity: 50,
      average_cost: 150.00,
      current_price: 185.25,
      current_value: 9262.50,
      total_cost: 7500.00,
      unrealized_gain_loss: 1762.50,
      unrealized_gain_loss_pct: 23.5,
      currency: 'USD'
    },
    {
      id: 2,
      security: { symbol: 'GOOGL', name: 'Alphabet Inc.' },
      platform: { name: 'Trading 212', account_type: 'Invest' },
      quantity: 25,
      average_cost: 120.00,
      current_price: 145.80,
      current_value: 3645.00,
      total_cost: 3000.00,
      unrealized_gain_loss: 645.00,
      unrealized_gain_loss_pct: 21.5,
      currency: 'USD'
    },
    {
      id: 3,
      security: { symbol: 'MSFT', name: 'Microsoft Corporation' },
      platform: { name: 'Freetrade', account_type: 'ISA' },
      quantity: 40,
      average_cost: 280.00,
      current_price: 265.50,
      current_value: 10620.00,
      total_cost: 11200.00,
      unrealized_gain_loss: -580.00,
      unrealized_gain_loss_pct: -5.18,
      currency: 'USD'
    },
    {
      id: 4,
      security: { symbol: 'TSLA', name: 'Tesla Inc.' },
      platform: { name: 'Interactive Brokers', account_type: 'General' },
      quantity: 20,
      average_cost: 250.00,
      current_price: 220.75,
      current_value: 4415.00,
      total_cost: 5000.00,
      unrealized_gain_loss: -585.00,
      unrealized_gain_loss_pct: -11.7,
      currency: 'USD'
    },
  ];

  useEffect(() => {
    setPortfolios(samplePortfolios);
    setHoldings(sampleHoldings);
    setSelectedPortfolio(samplePortfolios[0]);
  }, []);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const filteredAndSortedHoldings = holdings
    .filter(holding => {
      const matchesSearch = holding.security.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           holding.security.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesPlatform = filterPlatform === 'all' || holding.platform.name === filterPlatform;
      return matchesSearch && matchesPlatform;
    })
    .sort((a, b) => {
      let aVal, bVal;
      switch (sortField) {
        case 'symbol':
          aVal = a.security.symbol;
          bVal = b.security.symbol;
          break;
        case 'value':
          aVal = a.current_value;
          bVal = b.current_value;
          break;
        case 'gain_loss':
          aVal = a.unrealized_gain_loss;
          bVal = b.unrealized_gain_loss;
          break;
        case 'gain_loss_pct':
          aVal = a.unrealized_gain_loss_pct;
          bVal = b.unrealized_gain_loss_pct;
          break;
        default:
          aVal = a.current_value;
          bVal = b.current_value;
      }

      if (typeof aVal === 'string') {
        return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });

  const platforms = [...new Set(holdings.map(h => h.platform.name))];

  const formatCurrency = (value, currency = 'GBP') => {
    return new Intl.NumberFormat('en-GB', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
    }).format(value);
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <SortAsc className="h-4 w-4 text-gray-400" />;
    return sortDirection === 'asc' ? 
      <SortAsc className="h-4 w-4 text-blue-600" /> : 
      <SortDesc className="h-4 w-4 text-blue-600" />;
  };

  return (
    <div className="space-y-6">
      {/* Portfolio Selector */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Portfolio Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {portfolios.map(portfolio => (
            <div
              key={portfolio.id}
              onClick={() => setSelectedPortfolio(portfolio)}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                selectedPortfolio?.id === portfolio.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <h3 className="font-medium text-gray-900">{portfolio.name}</h3>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatCurrency(portfolio.total_value)}
              </p>
              <div className="flex items-center mt-2">
                {portfolio.total_value >= portfolio.total_cost ? (
                  <TrendingUp className="h-4 w-4 text-green-600 mr-1" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600 mr-1" />
                )}
                <span className={`text-sm font-medium ${
                  portfolio.total_value >= portfolio.total_cost ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(portfolio.total_value - portfolio.total_cost)}
                  ({(((portfolio.total_value - portfolio.total_cost) / portfolio.total_cost) * 100).toFixed(2)}%)
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Holdings Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              Holdings - {selectedPortfolio?.name}
            </h3>
            <div className="mt-4 sm:mt-0 flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search holdings..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              {/* Platform Filter */}
              <select
                value={filterPlatform}
                onChange={(e) => setFilterPlatform(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Platforms</option>
                {platforms.map(platform => (
                  <option key={platform} value={platform}>{platform}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  onClick={() => handleSort('symbol')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  <div className="flex items-center">
                    Security
                    <SortIcon field="symbol" />
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Platform
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Cost
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Price
                </th>
                <th
                  onClick={() => handleSort('value')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  <div className="flex items-center">
                    Market Value
                    <SortIcon field="value" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('gain_loss')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  <div className="flex items-center">
                    Gain/Loss
                    <SortIcon field="gain_loss" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('gain_loss_pct')}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  <div className="flex items-center">
                    Return %
                    <SortIcon field="gain_loss_pct" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedHoldings.map((holding) => (
                <tr key={holding.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {holding.security.symbol}
                      </div>
                      <div className="text-sm text-gray-500">
                        {holding.security.name}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm text-gray-900">{holding.platform.name}</div>
                      <div className="text-sm text-gray-500">{holding.platform.account_type}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {holding.quantity.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(holding.average_cost, holding.currency)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(holding.current_price, holding.currency)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {formatCurrency(holding.current_value, holding.currency)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-sm font-medium ${
                      holding.unrealized_gain_loss >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {holding.unrealized_gain_loss >= 0 ? '+' : ''}
                      {formatCurrency(holding.unrealized_gain_loss, holding.currency)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      holding.unrealized_gain_loss_pct >= 0
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {holding.unrealized_gain_loss_pct >= 0 ? '+' : ''}
                      {holding.unrealized_gain_loss_pct.toFixed(2)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredAndSortedHoldings.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No holdings found matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PortfolioView;