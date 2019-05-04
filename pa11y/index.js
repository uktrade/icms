// An example of running Pa11y programmatically, reusing
// existing Puppeteer browsers and pages
'use strict';

const html = require('/usr/local/lib/node_modules/pa11y-reporter-html');
const pa11y = require('/usr/local/lib/node_modules/pa11y');
const fs = require('fs');

const config = {
  chromeLaunchConfig: {
    args: ['--no-sandbox']
  }
};

function saveReport(html,name) {
  let filename="/reports/" + name + ".html";
  fs.writeFile(filename, html, function(err){
    if(err) throw err;
    console.log("Saved" + filename);
  });
}

function report(url, name) {
  pa11y(url,config).then(async results => {
    // Returns a string with the results formatted as HTML
    const htmlResults = await html.results(results);
    saveReport(htmlResults, name);
  });
}

report('http://web:8080', 'login');
