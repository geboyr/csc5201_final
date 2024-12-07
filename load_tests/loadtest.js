import http from 'k6/http';
import { sleep, check } from 'k6';

export let options = {
  vus: 50,          // number of virtual users (VU)
  duration: '10s',  // how long to run the test
};

// Store ingredient IDs added by this VU
let addedIngredientIDs = [];

const headers = __ENV.OUTGOING_API_KEY ? { 'Authorization': `ApiKey ${__ENV.OUTGOING_API_KEY}`, 'Content-Type': 'application/json' }
                              : { 'Content-Type': 'application/json' };

export default function () {
  // 1. GET ingredients
  let getRes = http.get('http://ingredients-service:5000/ingredients', { headers });
  check(getRes, {
    'GET /ingredients status is 200': (r) => r.status === 200,
  });

  sleep(0.1);

  // 2. POST a new ingredient
  let newIngredientName = 'ingredient-' + __VU + '-' + __ITER; // create a unique name per iteration
  let postPayload = JSON.stringify({ name: newIngredientName });
  let postRes = http.post('http://ingredients-service:5000/ingredients', postPayload, { headers });
  check(postRes, {
    'POST /ingredients status is 200 or 201': (r) => r.status === 200 || r.status === 201,
  });

  let createdIngredient;
  try {
    createdIngredient = JSON.parse(postRes.body);
  } catch (e) {
    // TODO
  }

  if (createdIngredient && createdIngredient.id) {
    addedIngredientIDs.push(createdIngredient.id);
  }

  sleep(0.1);

  // 3. DELETE an ingredient
  if (addedIngredientIDs.length > 0) {
    let idToDelete = addedIngredientIDs.shift(); // remove from the array
    let deleteRes = http.del(`http://ingredients-service:5000/ingredients/${idToDelete}`, null, { headers });
    check(deleteRes, {
      'DELETE /ingredients/<id> status is 204': (r) => r.status === 204
    });
  }

  sleep(0.1);
}
