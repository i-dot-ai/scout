
import { NextApiRequest, NextApiResponse } from 'next'
import { filterHeaderForAWSValues } from '@/utils/header'

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
): Promise<void> {
    const {
        body,
        method,
        headers,
    } = req
    switch (method) {
        case 'POST':
            try {
                const data = {
                    method: 'POST',
                    headers: {
                        ...filterHeaderForAWSValues(headers),
                        'Content-Type': 'application/json'
                    },
                    body: body
                }
                const response = await fetch(process.env.BACKEND_HOST + '/api/rate', data);
                if (!response.ok) {
                    console.error(await response.text())
                    console.error(await response.json())
                    throw new Error('Failed to read items by attribute');
                }
                res.status(200).send(await response.json())
            } catch (error) {
                let message
                console.log(error)
                if (error instanceof Error) message = error.message
                res.status(500).send({ error: message })
            }
            break
        default:
            res.setHeader('Allow', ['GET'])
            res.status(405).end(`Method ${method} Not Allowed`)
            break
    }
}
