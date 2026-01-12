import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
    try {
        // Read the analysis results file from the project root
        const analysisPath = path.join(process.cwd(), '..', 'analysis_results.json');

        if (!fs.existsSync(analysisPath)) {
            return NextResponse.json({
                status: 'not_found',
                message: 'No analysis available. Run python analyze_spending.py to generate.',
                timestamp: null,
                analysis: null,
            });
        }

        const data = fs.readFileSync(analysisPath, 'utf-8');
        const results = JSON.parse(data);

        return NextResponse.json(results);
    } catch (error) {
        console.error('Error reading analysis:', error);
        return NextResponse.json({
            status: 'error',
            message: 'Failed to load analysis results',
            error: String(error),
        }, { status: 500 });
    }
}
