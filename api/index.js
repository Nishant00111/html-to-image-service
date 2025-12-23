module.exports = (req, res) => {
  res.status(200).json({
    status: 'ok',
    message: 'HTML to Image Service is running',
    routes: ['/api/screenshot'],
  });
};
