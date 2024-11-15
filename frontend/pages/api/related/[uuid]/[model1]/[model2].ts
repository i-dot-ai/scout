
import { NextApiRequest, NextApiResponse } from 'next'
import { filterHeaderForAWSValues } from '@/utils/header';

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
): Promise<void> {
    const {
        query: { uuid, model1, model2, limit_to_user },
        method,
        headers
    } = req
    switch (method) {
        case 'GET':
            try {
                const data = {
                    method: 'GET',
                    headers: {
                        ...filterHeaderForAWSValues(headers), // Filter out cookies (not needed for backend requests
                    } as HeadersInit,
                }
                const response = await fetch(process.env.BACKEND_HOST + '/api/related/' + uuid + '/' + model1 + '/' + model2 + '?limit_to_user=' + limit_to_user, data);
                if (!response.ok) {
                    console.error(await response.text())
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
