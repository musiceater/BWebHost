class Status:
	Continue = 100
	SwitchingProtocols = 101
	Processing = 102					# WebDAV
	OK = 200
	Created = 201
	Accepted = 202
	NonAuthoritativeInformation = 203
	NoContent = 204
	ResetContent = 205
	PartialContent = 206
	Multistatus = 207				   # WebDAV
	MultipleChoices = 300
	MovedPermanently = 301
	MovedTemporarilty = 302
	SeeOther = 303
	NotModified = 304
	UseProxy = 305
	SwitchProxy = 306
	BadRequest = 400
	Unauthorized = 401
	PaymentRequired = 402
	Forbidden = 403
	NotFound = 404
	NotAllowed = 405
	NotAcceptable = 406
	ProxyAuthenticationRequired = 407
	RequestTimeout = 408
	Conflict = 409
	Gone = 410
	LengthRequired = 411
	PreconditionFailed = 412
	RequestEntityTooLarge = 413
	RequestURITooLong = 414			 
	URITooLong = 414					# synonym
	UnsupportedMediaType = 415
	RquestedRangeNotValid = 416
	ExpectationFailed = 419
	UnprocessableEntity = 422		   # WebDAV
	Locked = 423						# WebDAV
	FailedDependency = 424				 # WebDAV
	InsufficientSpaceOnResource = 425   # WebDAV (draft 8 and earlier)
	InternalServerError = 500
	NotImplemented = 501
	BadGateway = 502
	ServiceUnavailable = 503
	GatewayTimeout = 504
	HTTPVersionNotSupported = 505
	RedirectionFailed = 506
	InsufficientStorage = 507		   # WebDAV draft 9 and on

HTTP_Response_Code = {
	100: "Continue",
	101: "Switching Protocols",
	102: "Processing",				  # WebDAV
	200: "OK",
	201: "Created",
	202: "Accepted",
	203: "Non-Authorative Information",
	204: "No Content",
	205: "Reset Content",
	206: "Partial Contents",
	207: "Multi-Status",				# WebDAV
	300: "Multiple Choices",
	301: "Moved Permanently",
	302: "Temporary relocation URL follows",
	303: "Method (use a different method)",
	304: "Not Modified",
	305: "Use Proxy",
	400: "Bad request",
	401: "Unauthorized",
	402: "Payment required",
	403: "Forbidden",
	404: "Not found",
	405: "Method not allowed",
	406: "Not Acceptable",
	407: "Proxy Authentication Required",
	408: "Request Time-Out",
	409: "Conflict",
	410: "Gone",
	411: "Length Required",
	412: "Precondition Failed",
	413: "Request Entity Too Large",
	414: "Request-URI Too Large",
	415: "Unsupported Media Type",
	416: "Requested range not valid",
	418: "code 418",
	419: "code 419",
	420: "code 420",
	421: "Destination Locked",
	422: "Unprocessable Entity",		# WebDAV
	423: "Locked",
	424: "Failed Dependency",
	425: "Insufficient Space on Resource",
	500: "Internal server error",
	501: "Not implemented",
	502: "Bad Gateway",
	503: "Service Unavailable",
	504: "Gateway Time-out",
	505: "HTTP Version not supported",
	506: "Redirection Failed",
	507: "Insufficient Storage"
	}
