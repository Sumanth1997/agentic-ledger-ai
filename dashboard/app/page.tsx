'use client';

import { useEffect, useState } from 'react';
import { supabase, Transaction } from '@/lib/supabase';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
} from 'recharts';

// Helper to get category from transaction (uses database category)

const COLORS = ['#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#3B82F6', '#8B5CF6', '#EC4899'];

interface AIInsights {
  timestamp: string | null;
  analysis: string | null;
  status: string;
}

export default function Dashboard() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [aiInsights, setAiInsights] = useState<AIInsights | null>(null);
  const [showInsights, setShowInsights] = useState(false);

  useEffect(() => {
    async function fetchData() {
      const { data, error } = await supabase
        .from('transactions')
        .select('*')
        .order('transaction_date', { ascending: true });

      if (!error && data) {
        setTransactions(data);
      }
      setLoading(false);
    }

    async function fetchInsights() {
      try {
        const res = await fetch('/api/analysis');
        const data = await res.json();
        setAiInsights(data);
      } catch (e) {
        console.error('Failed to fetch AI insights:', e);
      }
    }

    fetchData();
    fetchInsights();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-slate-900 to-gray-950 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  // Calculate stats
  const debits = transactions.filter(t => t.transaction_type === 'debit');
  const credits = transactions.filter(t => t.transaction_type === 'credit');
  const totalSpending = debits.reduce((sum, t) => sum + Number(t.amount), 0);
  const totalCredits = credits.reduce((sum, t) => sum + Number(t.amount), 0);
  const avgTransaction = debits.length > 0 ? totalSpending / debits.length : 0;

  // Monthly spending data
  const monthlyData = transactions.reduce((acc, t) => {
    if (t.transaction_type !== 'debit') return acc;
    const month = t.transaction_date.substring(0, 7); // YYYY-MM
    const existing = acc.find(m => m.month === month);
    if (existing) {
      existing.amount += Number(t.amount);
    } else {
      acc.push({ month, amount: Number(t.amount) });
    }
    return acc;
  }, [] as { month: string; amount: number }[]).sort((a, b) => a.month.localeCompare(b.month));

  // Category data
  const categoryData = debits.reduce((acc, t) => {
    const category = t.category || 'Uncategorized';
    const existing = acc.find(c => c.name === category);
    if (existing) {
      existing.value += Number(t.amount);
    } else {
      acc.push({ name: category, value: Number(t.amount) });
    }
    return acc;
  }, [] as { name: string; value: number }[]).sort((a, b) => b.value - a.value);

  // Credits vs Debits by month
  const comparisonData = transactions.reduce((acc, t) => {
    const month = t.transaction_date.substring(0, 7);
    const existing = acc.find(m => m.month === month);
    const amount = Number(t.amount);
    if (existing) {
      if (t.transaction_type === 'debit') existing.debits += amount;
      else existing.credits += amount;
    } else {
      acc.push({
        month,
        debits: t.transaction_type === 'debit' ? amount : 0,
        credits: t.transaction_type === 'credit' ? amount : 0,
      });
    }
    return acc;
  }, [] as { month: string; debits: number; credits: number }[]).sort((a, b) => a.month.localeCompare(b.month));

  // Recent transactions
  const recentTransactions = [...transactions]
    .sort((a, b) => b.transaction_date.localeCompare(a.transaction_date))
    .slice(0, 10);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-slate-900 to-gray-950 p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">
          💳 Transaction Dashboard
        </h1>
        <p className="text-slate-400">Zolve Credit Card Analytics</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Spending"
          value={`$${totalSpending.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          subtitle="All debit transactions"
          color="from-red-500 to-pink-500"
        />
        <StatCard
          title="Total Credits"
          value={`$${totalCredits.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
          subtitle="Payments & refunds"
          color="from-green-500 to-emerald-500"
        />
        <StatCard
          title="Transactions"
          value={transactions.length.toString()}
          subtitle={`${debits.length} debits, ${credits.length} credits`}
          color="from-blue-500 to-cyan-500"
        />
        <StatCard
          title="Avg Transaction"
          value={`$${avgTransaction.toFixed(2)}`}
          subtitle="Per debit transaction"
          color="from-slate-600 to-slate-500"
        />
      </div>

      {/* AI Insights Panel */}
      {aiInsights && aiInsights.status === 'completed' && (
        <div className="bg-gradient-to-r from-cyan-900/30 to-slate-800/50 backdrop-blur-lg rounded-2xl p-6 border border-cyan-500/30 mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🤖</span>
              <h2 className="text-xl font-semibold text-white">AI Insights</h2>
              <span className="px-2 py-1 rounded-full text-xs bg-green-500/30 text-green-200">
                Powered by Ollama
              </span>
            </div>
            <div className="flex items-center gap-4">
              {aiInsights.timestamp && (
                <span className="text-slate-400 text-sm">
                  Updated: {new Date(aiInsights.timestamp).toLocaleString()}
                </span>
              )}
              <button
                onClick={() => setShowInsights(!showInsights)}
                className="px-4 py-2 bg-cyan-500/30 hover:bg-cyan-500/50 text-white rounded-lg transition-colors"
              >
                {showInsights ? 'Hide Details' : 'Show Details'}
              </button>
            </div>
          </div>

          {showInsights && aiInsights.analysis && (
            <div className="bg-black/20 rounded-xl p-4 max-h-96 overflow-y-auto">
              <pre className="text-slate-200 text-sm whitespace-pre-wrap font-mono">
                {aiInsights.analysis}
              </pre>
            </div>
          )}

          {!showInsights && (
            <p className="text-slate-300 text-sm">
              Click &quot;Show Details&quot; to view spending analysis, budget recommendations, and anomaly detection.
            </p>
          )}
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Monthly Spending Trend */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
          <h2 className="text-xl font-semibold text-white mb-4">📈 Monthly Spending</h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={monthlyData}>
              <defs>
                <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#06B6D4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
              <XAxis dataKey="month" stroke="#ffffff80" tick={{ fill: '#ffffff80' }} />
              <YAxis stroke="#ffffff80" tick={{ fill: '#ffffff80' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
                labelStyle={{ color: '#ffffff' }}
              />
              <Area
                type="monotone"
                dataKey="amount"
                stroke="#06B6D4"
                fillOpacity={1}
                fill="url(#colorAmount)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Category Breakdown */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
          <h2 className="text-xl font-semibold text-white mb-4">🥧 Spending by Category</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {categoryData.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
                formatter={(value) => [`$${Number(value).toFixed(2)}`, 'Amount']}
              />
              <Legend
                wrapperStyle={{ color: '#ffffff' }}
                formatter={(value) => <span className="text-white">{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Credits vs Debits Chart */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 mb-8">
        <h2 className="text-xl font-semibold text-white mb-4">📊 Credits vs Debits</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={comparisonData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
            <XAxis dataKey="month" stroke="#ffffff80" tick={{ fill: '#ffffff80' }} />
            <YAxis stroke="#ffffff80" tick={{ fill: '#ffffff80' }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
              formatter={(value) => [`$${Number(value).toFixed(2)}`]}
            />
            <Legend wrapperStyle={{ color: '#ffffff' }} />
            <Bar dataKey="debits" fill="#EF4444" name="Spending" radius={[4, 4, 0, 0]} />
            <Bar dataKey="credits" fill="#10B981" name="Credits" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Transactions Table */}
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
        <h2 className="text-xl font-semibold text-white mb-4">📋 Recent Transactions</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-slate-400 border-b border-white/20">
                <th className="pb-3 font-medium">Date</th>
                <th className="pb-3 font-medium">Description</th>
                <th className="pb-3 font-medium">Category</th>
                <th className="pb-3 font-medium text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {recentTransactions.map((tx) => (
                <tr key={tx.id} className="border-b border-white/10 hover:bg-white/5">
                  <td className="py-3 text-white">{tx.transaction_date}</td>
                  <td className="py-3 text-white truncate max-w-xs">{tx.description}</td>
                  <td className="py-3">
                    <span className="px-2 py-1 rounded-full text-xs bg-cyan-500/30 text-cyan-200">
                      {tx.category || 'Uncategorized'}
                    </span>
                  </td>
                  <td className={`py-3 text-right font-medium ${tx.transaction_type === 'credit' ? 'text-green-400' : 'text-red-400'
                    }`}>
                    {tx.transaction_type === 'credit' ? '+' : '-'}${Number(tx.amount).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  subtitle,
  color,
}: {
  title: string;
  value: string;
  subtitle: string;
  color: string;
}) {
  return (
    <div className={`bg-gradient-to-br ${color} rounded-2xl p-6 shadow-xl`}>
      <p className="text-white/80 text-sm font-medium mb-1">{title}</p>
      <p className="text-3xl font-bold text-white mb-1">{value}</p>
      <p className="text-white/60 text-sm">{subtitle}</p>
    </div>
  );
}
