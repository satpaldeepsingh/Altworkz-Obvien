var personFields = [
  "biographies",
  "names",
  "emailAddresses",
  "organizations",
  "phoneNumbers",
  "photos",
];
// Client ID and API key from the Developer Console
var CLIENT_ID =
  "368943706935-vesr69v412fqaccj7pepnh310jf05rla.apps.googleusercontent.com";
var API_KEY = "JfwjEOt3hOTMx3Szrhwacbj5";

// Array of API discovery doc URLs for APIs used by the quickstart
var DISCOVERY_DOCS = [
  "https://www.googleapis.com/discovery/v1/apis/people/v1/rest",
];

// Authorization scopes required by the API; multiple scopes can be
// included, separated by spaces.
var SCOPES = "https://www.googleapis.com/auth/contacts.readonly";

var authorizeButton = document.getElementById("authorize_button");
var signoutButton = document.getElementById("signout_button");

/**
 *  On load, called to load the auth2 library and API client library.
 */
function handleClientLoad() {
  gapi.load("client:auth2", initClient);
}

/**
 *  Initializes the API client library and sets up sign-in state
 *  listeners.
 */
function initClient() {
  gapi.client
    .init({
      apiKey: API_KEY,
      clientId: CLIENT_ID,
      discoveryDocs: DISCOVERY_DOCS,
      scope: SCOPES,
    })
    .then(
      function () {
        // Listen for sign-in state changes.
        gapi.auth2.getAuthInstance().isSignedIn.listen(updateSigninStatus);

        // Handle the initial sign-in state.
        updateSigninStatus(gapi.auth2.getAuthInstance().isSignedIn.get());
        authorizeButton.onclick = handleAuthClick;
        signoutButton.onclick = handleSignoutClick;
      },
      function (error) {
        console.log(JSON.stringify(error, null, 2));
      }
    );
}

/**
 *  Called when the signed in status changes, to update the UI
 *  appropriately. After a sign-in, the API is called.
 */
function updateSigninStatus(isSignedIn) {
  if (isSignedIn) {
    authorizeButton.style.display = "none";
    signoutButton.style.display = "block";
    listConnectionNames();
  } else {
    authorizeButton.style.display = "block";
    signoutButton.style.display = "none";
  }
}

/**
 *  Sign in the user upon button click.
 */
function handleAuthClick(event) {
  gapi.auth2.getAuthInstance().signIn();
}

/**
 *  Sign out the user upon button click.
 */
function handleSignoutClick(event) {
  gapi.auth2.getAuthInstance().signOut();
  location.reload();
}

/**
 * Print the display name if available for 10 connections.
 */

var data = [];
var connections = [];

function listConnectionNames() {
  gapi.client.people.people.connections
    .list({
      resourceName: "people/me",
      pageSize: 1000,
      personFields: personFields,
    })
    .then(function (response) {
      connections = response.result.connections;
      if (typeof connections !== "undefined" && connections.length > 0) {
        for (i = 0; i < connections.length; i++) {
          var connectionData = [];
          var person = connections[i];
          if (person.photos && person.photos.length > 0) {
            connectionData["Photo"] =
              "<img src=" + person.photos[0].url + " />";
          } else {
            connectionData["Photo"] = "N/A";
          }

          if (person.names && person.names.length > 0) {
            connectionData["Name"] = person.names[0].displayName;
          } else {
            connectionData["Name"] = "N/A";
          }

          if (person.emailAddresses && person.emailAddresses.length > 0) {
            connectionData["Email"] = person.emailAddresses[0].value;
          } else {
            connectionData["Email"] = "N/A";
          }
          if (person.organization && person.organization.length > 0) {
            connectionData["Organization"] = person.organization[0].name;
          } else {
            connectionData["Organization"] = "N/A";
          }
          if (person.biographies && person.biographies.length > 0) {
            connectionData["Biography"] = person.biographies[0].value;
          } else {
            connectionData["Biography"] = "N/A";
          }

          data.push(connectionData);
        }

        $("#peoples").DataTable().destroy();
        $("#peoples").DataTable({
          scrollY: 300,
          scrollX: true,
          scrollCollapse: true,
          paging: false,
          data: data,
          columns: [
            { data: "Photo" },
            { data: "Name" },
            { data: "Email" },
            { data: "Organization" },
            { data: "Biography" },
          ],
        });
      } else {
        alert("No connections found.");
      }
    });
}
