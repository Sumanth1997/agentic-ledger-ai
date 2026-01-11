import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseKey);

export type Transaction = {
    id: string;
    statement_id: string;
    posted_date: string;
    transaction_date: string;
    description: string;
    amount: number;
    transaction_type: 'credit' | 'debit';
    created_at: string;
};

export async function getTransactions(): Promise<Transaction[]> {
    const { data, error } = await supabase
        .from('transactions')
        .select('*')
        .order('transaction_date', { ascending: false });

    if (error) throw error;
    return data || [];
}

export async function getTransactionStats() {
    const { data, error } = await supabase
        .from('transactions')
        .select('*');

    if (error) throw error;

    const transactions = data || [];

    const debits = transactions.filter(t => t.transaction_type === 'debit');
    const credits = transactions.filter(t => t.transaction_type === 'credit');

    return {
        totalSpending: debits.reduce((sum, t) => sum + Number(t.amount), 0),
        totalCredits: credits.reduce((sum, t) => sum + Number(t.amount), 0),
        transactionCount: transactions.length,
        avgTransaction: transactions.length > 0
            ? debits.reduce((sum, t) => sum + Number(t.amount), 0) / debits.length
            : 0,
    };
}
