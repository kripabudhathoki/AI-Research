/**
 * Automated Verification Test for Research Brief Multi-Agent App
 */

const http = require('http');

async function runTests() {
  console.log('--- Starting Multi-Agent App Verification Tests ---');

  process.env.PORT = '4005';
  require('../server.js');

  await new Promise(r => setTimeout(r, 600));

  function request(options, postData) {
    return new Promise((resolve, reject) => {
      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', chunk => { data += chunk; });
        res.on('end', () => resolve({ statusCode: res.statusCode, data, headers: res.headers }));
      });
      req.on('error', reject);
      if (postData) req.write(postData);
      req.end();
    });
  }

  try {
    // Test 1: GET /
    console.log('[Test 1] Testing static root GET / ...');
    const rootRes = await request({
      hostname: '127.0.0.1',
      port: 4005,
      path: '/',
      method: 'GET'
    });
    if (rootRes.statusCode !== 200 || !rootRes.data.includes('Research Brief')) {
      throw new Error(`Root test failed: Status ${rootRes.statusCode}`);
    }
    console.log('✅ [Test 1 Passed] Root index.html served successfully.');

    // Test 2: GET /api/health
    console.log('[Test 2] Testing GET /api/health ...');
    const healthRes = await request({
      hostname: '127.0.0.1',
      port: 4005,
      path: '/api/health',
      method: 'GET'
    });
    const healthData = JSON.parse(healthRes.data);
    if (healthRes.statusCode !== 200 || healthData.status !== 'ok') {
      throw new Error(`Health check failed: ${healthRes.data}`);
    }
    console.log('✅ [Test 2 Passed] Health check OK.');

    // Test 3: POST /api/research for Nepal food delivery query
    console.log('[Test 3] Testing POST /api/research for "Analyze the food delivery market in Nepal." ...');
    const queryPayload = JSON.stringify({
      query: 'Analyze the food delivery market in Nepal.',
      sample: false
    });
    const researchRes = await request({
      hostname: '127.0.0.1',
      port: 4005,
      path: '/api/research',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(queryPayload)
      }
    }, queryPayload);

    if (researchRes.statusCode !== 200) {
      throw new Error(`Research request failed: Status ${researchRes.statusCode}, body: ${researchRes.data}`);
    }

    const resJson = JSON.parse(researchRes.data);
    if (!resJson.success || !resJson.result) {
      throw new Error('Research failed: success != true');
    }

    const result = resJson.result;
    console.log(`\n📋 Research Brief Generated for: "${result.entity}"`);
    console.log(`- Competitors: ${result.final.competitors.map(c => c.name).join(', ')}`);
    console.log(`- Observations count: ${result.final.obs.length}`);
    console.log(`- Sources count: ${result.sources.length}`);
    console.log(`- Revisions: ${result.rev}`);

    if (!result.final.summary || !result.final.competitors.length || !result.final.obs.length) {
      throw new Error('Missing core brief sections (summary, competitors, or observations)');
    }

    // Verify competitor count constraint (up to 2)
    if (result.final.competitors.length > 2) {
      throw new Error('Exceeded maximum of 2 competitors');
    }

    console.log(`✅ [Test 3 Passed] Real research brief successfully generated!`);

    // Test 4: Dynamic topic test (Tesla)
    console.log('\n[Test 4] Testing live dynamic research for "Tesla" ...');
    const teslaPayload = JSON.stringify({ query: 'Tesla', sample: false });
    const teslaRes = await request({
      hostname: '127.0.0.1',
      port: 4005,
      path: '/api/research',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(teslaPayload)
      }
    }, teslaPayload);

    const teslaJson = JSON.parse(teslaRes.data);
    if (!teslaJson.success || !teslaJson.result.final.competitors.length) {
      throw new Error('Failed to generate dynamic research for Tesla');
    }
    console.log(`- Entity: "${teslaJson.result.entity}"`);
    console.log(`- Competitors: ${teslaJson.result.final.competitors.map(c => c.name).join(', ')}`);
    console.log('✅ [Test 4 Passed] Dynamic topic research verified.');

    console.log('\n=============================================');
    console.log('🎉 ALL MULTI-AGENT APP TESTS PASSED!');
    console.log('=============================================\n');
    process.exit(0);
  } catch (err) {
    console.error('❌ Test failed with error:', err);
    process.exit(1);
  }
}

runTests();
