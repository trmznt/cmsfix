
<nav class="navbar navbar-expand-md navbar-dark bg-dark mb-4">
	<a class="navbar-brand" href="/">${request.get_resource('cmsfix.title', 'CMSFix')}</a>
    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarCollapse" aria-controls="navbarCollapse" aria-expanded="false" aria-label="Toggle navigation">
    	<span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse justify-content-stretch" id="navbarCollapse">
        <div class="navbar-nav mr-auto"></div>
        <div class="navbar-nav justify-content-stretch">
    	<form class="mr-3 d-inline" action='/search'>
            <div class="input-group">
    		<input class="form-control" type="text" placeholder="Search" aria-label="Search" name='q'>
    		<button class="btn btn-outline-success my-2 my-sm-0" type="submit"><i class="fa fa-search"></i></button>
            </div>
        </form>
    	${user_menu(request)}
        </div>
    </div>
</nav>
