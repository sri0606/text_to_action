const axios = require('axios');

class CalculatorInstance {
  constructor() {}

  add(items) {
    return items.reduce((sum, item) => sum + Number(item), 0);
  }

  subtract(a, b) {
    return Number(a) - Number(b);
  }

  multiply(items) {
    return items.reduce((product, item) => product * Number(item), 1);
  }

  divide(a, b) {
    if (Number(b) === 0) {
      throw new Error("Cannot divide by zero");
    }
    return Number(a) / Number(b);
  }
}

const calculatorInstance = new CalculatorInstance();

async function runExtraction(userInput){
      // Send a request to the server to extract functions and their arguments
    const extractFunctionsResponse = await axios.post('http://localhost:8000/extract_actions_with_args', {
      text: userInput,
      top_k: 1,
      threshold: 0.45,
    });
    // Extract the function and its arguments from the response
    const result = JSON.parse(extractFunctionsResponse.data);
    return result;
}

async function runExecution(extractionResults) {
  let results = [];

  try {
    const actions = extractionResults.actions; // Array of actions

    for (const action of actions) {
      const functionName = action.action; // e.g., "add", "resize_video"
      const functionArgs = action.args; // e.g., {values: [3, 4]} or {width: 480, height: 720}


      console.log(`Executing function: ${functionName} with args:`, functionArgs);

      // Check if the method exists on the instance
      if (typeof calculatorInstance[functionName] === 'function') {
        // Call the method on the class instance
        const result = await executeFunction(functionName, functionArgs);
        results.push({
          status: 'success', 
          actionName: action.action,
          output: result
        });
      } else {
        results.push({
          status: 'error', 
          message: `Function ${functionName} not found`
        });
      }
    }

  } catch (error) {
    console.error('Error in runExecution:', error);
    return {status: "error", message: `Error: ${error.message}`};
  }

  return {results: results, message: extractionResults.message};
}

async function executeFunction(functionName, functionArgs) {
  try {
    const args = Array.isArray(functionArgs) ? functionArgs : Object.values(functionArgs);
    const result = calculatorInstance[functionName](...args);
    console.log(`Result of ${functionName}:`, result);
    return result;
  } catch (error) {
    console.error(`Error in executing ${functionName}:`, error);
    throw error;
  }
}

async function processQuery(query) {
  try {
    console.log(`Processing query: "${query}"`);
    const extractionResult = await runExtraction(query);
    if (extractionResult) {
      console.log('Extraction result:', extractionResult);
      const executionResult = await runExecution(extractionResult);
      console.log('Execution result:', executionResult);
    } else {
      console.log('No function extracted from the query.');
    }
  } catch (error) {
    console.error('Error processing query:', error.message);
  }
  console.log('---');
}

// Sample queries
const sampleQueries = [
  "add 3, 5",
  "subtract 10 from 20",
  "multiply 4, 5, 6",
  "divide 100 by 5",
];

// Run the demo
async function runDemo() {
  for (const query of sampleQueries) {
    await processQuery(query);
  }
}

runDemo();