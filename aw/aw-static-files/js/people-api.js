var personFields = [
  "biographies",
  "names",
  "phoneNumbers",
  "emailAddresses",
  "organizations",
  "photos",
];
// Client ID and API key from the Developer Console
var CLIENT_ID =
  "368943706935-vesr69v412fqaccj7pepnh310jf05rla.apps.googleusercontent.com";
var API_KEY = "AIzaSyBaI9Un3eul2PFZRE6-xdwMdJ1XCZcsl1s";

// Array of API discovery doc URLs for APIs used by the quickstart
var DISCOVERY_DOCS = [
  "https://www.googleapis.com/discovery/v1/apis/people/v1/rest",
];

// Authorization scopes required by the API; multiple scopes can be
// included, separated by spaces.
var SCOPES = "https://www.googleapis.com/auth/contacts.readonly";

var authorizeButton = document.getElementById("authorize_button");
var signoutButton = document.getElementById("signout_button");
var importButton = document.getElementById("import-contacts");
var importButtonLabel = document.getElementById("label_import_contacts");

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
    importButton.style.display = "block";
    signoutButton.style.display = "block";
    listConnectionNames();
    importButtonLabel.style.display = "block";
  } else {
    authorizeButton.style.display = "block";
    signoutButton.style.display = "none";
    importButton.style.display = "none";
    importButtonLabel.style.display = "none";
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
var table;
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
      if (connections.length > 0) {
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
            if (person.names[0].displayName && person.names[0].displayName.length > 0) {
                connectionData["Name"] = person.names[0].displayName;
            } else {
                 connectionData["Name"] = "N/A";
            }
          } else {
            continue;
            connectionData["Name"] = "N/A";
          }

          if (person.phoneNumbers && person.phoneNumbers.length > 0) {
            if (person.phoneNumbers[0].value && person.phoneNumbers[0].value.length > 0) {
                connectionDataPhone = person.phoneNumbers[0].value;
                 if (ValidatePhone(connectionDataPhone) === true ) {
                    connectionData["Number"] = connectionDataPhone;
                 } else {
                    connectionData["Number"] = "N/A";
                 }
            } else {
                 connectionData["Number"] = "N/A";
            }

          } else {
            connectionData["Number"] = "N/A";
          }

          if (person.emailAddresses && person.emailAddresses.length > 0) {
             connectionDataEmail = person.emailAddresses[0].value;
             if (ValidateEmail(connectionDataEmail) === true ) {
                connectionData["Email"] = connectionDataEmail;
             } else {
                connectionData["Email"] = "N/A";
             }
          } else {
            connectionData["Email"] = "N/A";
          }
          if (person.organizations && person.organizations.length > 0) {
            if (person.organizations[0].name && person.organizations[0].name.length > 0) {
                connectionData["Organization"] = person.organizations[0].name;
            } else {
                 connectionData["Organization"] = "N/A";
            }
          } else {
            connectionData["Organization"] = "N/A";
          }
          if (person.organizations && person.organizations.length > 0) {
            if (person.organizations[0].title && person.organizations[0].title.length > 0) {
                 connectionData["Job title"] = person.organizations[0].title;
            } else {
                 connectionData["Job title"] = "N/A";
            }

          } else {
            connectionData["Job title"] = "N/A";
          }
          if (person.names && person.names.length > 0) {
            connectionData["contactId"] = person.names[0].metadata.source.id;
            connections[i]['id'] = person.names[0].metadata.source.id;
          } else {

            connectionData["contactId"] = i;
          }
          data.push(connectionData);

        };
        $("#peoples").DataTable().destroy();
        table = $("#peoples").DataTable({
          data: data,
          columns: [
            { data: "contactId" },
            { data: "Photo" },
            { data: "Name" },
            { data: "Number" },
            { data: "Email" },
            { data: "Organization" },
            { data: "Job title" },
          ],
          columnDefs: [{
              targets: 0,
              searchable:false,
              orderable:false,
              className: 'dt-body-center',
              render: function (data, type, full, meta){
              return '<input type="checkbox" class="dt-checkboxes" name="id[]" value="'+data+'">';
              },
              checkboxes: {
                 selectRow: true,
                 selectAllPages : false,
          }
           }],

          select: {
             style: 'multi',
          },
          order: [[1, 'asc']]
        });

      } else {
        console.log("No connections found.");
      }
    });
}
function ValidateEmail(connectionDataEmail) {
    var mailformat = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
    if(connectionDataEmail.match(mailformat)) {
        return true;
    }
    else {
        return false;
    }
}
function ValidatePhone(connectionDataPhone) {
    var phoneformat = /^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$/;
    if(connectionDataPhone.match(phoneformat)) {
        return true;
    }
    else {
        return false;
    }
}