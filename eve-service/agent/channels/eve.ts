import { eveChannel } from 'eve/channels/eve';
import { timingSafeEqual } from 'node:crypto';

export default eveChannel({ auth: (request) => {
  const secret = process.env.OPS_EVE_TOKEN;
  const received = request.headers.get('authorization') || '';
  if (!secret) return null;
  const expected = Buffer.from(`Bearer ${secret}`);
  const actual = Buffer.from(received);
  if (actual.length !== expected.length || !timingSafeEqual(actual, expected)) return null;
  return { authenticator: 'ops-local', principalId: 'operator', principalType: 'user', attributes: {} };
} });
